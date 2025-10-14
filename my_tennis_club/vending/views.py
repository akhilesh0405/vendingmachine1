from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from decimal import Decimal
from .models import Product, TransactionLog

DENOMINATIONS = [100, 50, 20, 10, 5, 1]  # greedy order (largest -> smallest)

def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})


def purchase_form(request):
    """
    Shows a form to input:
      - product id
      - quantity
      - counts of each denomination (100,50,20,10,5,1)
    On POST it processes payment, gives change, logs transaction and shows result.
    """
    message = None
    context = {'products': Product.objects.all(), 'denominations': DENOMINATIONS}

    if request.method == 'POST':
        # read form fields
        try:
            product_id = int(request.POST.get('product_id'))
            qty = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            context['error'] = "Invalid product id or quantity."
            return render(request, 'purchase_form.html', context)

        product = get_object_or_404(Product, id=product_id)
        if qty <= 0:
            context['error'] = "Quantity must be 1 or more."
            return render(request, 'purchase_form.html', context)

        if product.quantity_left < qty:
            context['error'] = f"Not enough stock. Available: {product.quantity_left}"
            return render(request, 'purchase_form.html', context)

        # read denomination counts
        counts = {}
        total_inserted = Decimal('0.00')
        for d in DENOMINATIONS:
            raw = request.POST.get(f'denom_{d}', '0')
            try:
                c = int(raw) if raw != '' else 0
            except ValueError:
                c = 0
            if c < 0:
                c = 0
            counts[d] = c
            total_inserted += Decimal(d) * Decimal(c)

        total_price = Decimal(str(product.price)) * Decimal(qty)

        # not enough money
        if total_inserted < total_price:
            context['error'] = f"Insufficient funds. Price: Rs {total_price} but inserted Rs {total_inserted}."
            # show inserted breakdown and let user continue/exit
            context['inserted_breakdown'] = _format_breakdown(counts)
            context['product'] = product
            context['quantity'] = qty
            return render(request, 'purchase_form.html', context)

        # compute change amount
        change_amount = total_inserted - total_price
        change_breakdown = compute_change_breakdown(change_amount)

        # update stock
        product.quantity_left -= qty
        product.save()

        # prepare inserted_details string (only denominations with count>0)
        inserted_details = _format_breakdown(counts)  # e.g. "2x100,1x50"

        change_details = _format_breakdown(change_breakdown)

        # create transaction record
        TransactionLog.objects.create(
            date=timezone.now().date(),
            time=timezone.now().time(),
            amount_inserted=float(total_inserted),
            inserted_details=inserted_details,
            change_returned=float(change_amount),
            change_details=change_details
        )

        # prepare message and show result page
        message = (f"Purchased {product.name} x{qty}. Price: Rs {total_price}. "
                   f"Inserted: Rs {total_inserted}. Change returned: Rs {change_amount}.")
        return render(request, 'purchase_result.html', {
            'message': message,
            'inserted_details': inserted_details,
            'change_details': change_details,
            'continue_url': '/purchase/',  # the "continue other purchase" link
            'home_url': '/',
        })

    # GET -> show the form
    return render(request, 'purchase_form.html', context)


# keep the old quick-buy for direct buy links (optional)
def purchase_product(request, product_id):
    product = Product.objects.get(id=product_id)
    amount_inserted = Decimal('100.00')
    inserted_details = "1 x Rs100"
    change_returned = amount_inserted - Decimal(str(product.price))
    change_breakdown = compute_change_breakdown(change_returned)
    change_details = _format_breakdown(change_breakdown) if isinstance(change_breakdown, dict) else change_breakdown

    if product.quantity_left > 0:
        product.quantity_left -= 1
        product.save()

        TransactionLog.objects.create(
            date=timezone.now().date(),
            time=timezone.now().time(),
            amount_inserted=float(amount_inserted),
            inserted_details=inserted_details,
            change_returned=float(change_returned),
            change_details=change_details
        )
        message = f"Successfully purchased {product.name}! Change: Rs{change_returned}"
    else:
        message = f"Sorry, {product.name} is out of stock."

    return render(request, 'purchase_result.html', {'message': message, 'home_url': '/'})


# --------------------------
# Helper utilities
# --------------------------
def compute_change_breakdown(change_amount):
    """
    Given a Decimal change_amount (e.g. Decimal('37')), returns a dict {denom: count, ...}
    Uses greedy algorithm for denominations defined in DENOMINATIONS.
    """
    # avoid floating problems — convert to integer rupees (assumes denominations are whole rupees)
    change = int(round(float(change_amount)))
    breakdown = {}
    for d in DENOMINATIONS:
        cnt = change // d
        if cnt:
            breakdown[d] = int(cnt)
            change -= d * cnt
    return breakdown


def _format_breakdown(breakdown):
    """
    Accepts either:
      - dict {denom: count}
      - or counts dict for INSERTED counts (same format)
    Returns a human readable string like "2x100,1x50"
    """
    if not breakdown:
        return "None"
    if isinstance(breakdown, dict):
        parts = [f"{v}x{int(k)}" for k, v in breakdown.items() if v]
        return ", ".join(parts) if parts else "None"
    # if it's not dict, just return str
    return str(breakdown)
