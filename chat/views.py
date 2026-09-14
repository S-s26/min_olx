from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.core.paginator import Paginator

from chat.models import chatroom, message
from product.models import product
from activity.models import UserActivity


@login_required
def chat_list(request):
    """List every conversation the current user participates in."""
    user = request.user
    qs = (
        chatroom.objects
        .filter(buyer=user) | chatroom.objects.filter(seller=user)
    )
    # [OLD CODE - Commented out because it caused "Cannot filter a query once a slice has been taken" error]
    # qs = qs.select_related('product', 'buyer', 'seller').prefetch_related(
    #     Prefetch('message', queryset=message.objects.order_by('-created_at')[:1])
    # ).order_by('-updated_at')

    # [NEW CODE - Removed Prefetch slice; the model's @property handles last_message]
    qs = qs.select_related('product', 'buyer', 'seller').order_by('-updated_at')

    # Decorate each room with the "other" participant for the current user
    # so the template doesn't need to pass `request.user` to a method.
    rooms = []
    for room in qs:
        room.other_user = room.seller if room.buyer_id == user.id else room.buyer
        rooms.append(room)

    return render(request, 'chat_list.html', {'chatroom': rooms})


@login_required
def start_chat(request, p_id):
    """Open or create the chat between current user and the product seller."""
    product_d = get_object_or_404(product, id=p_id)
    seller = product_d.seller
    buyer = request.user
    if buyer == seller:
        return redirect('home')
    conversation, created = chatroom.objects.get_or_create(
        product=product_d, buyer=buyer, seller=seller
    )
    if created:
        UserActivity.record(
            buyer, UserActivity.EVENT_CHAT_OPEN,
            title=f'Started chat about “{product_d.title}”',
            detail=f'with {seller.username}',
        )
    return redirect('chat_detail', chatroom_id=conversation.id)


@login_required
def chat_details(request, chatroom_id):
    """Render the chat shell. Messages are pushed over WebSocket.

    The page only renders the *initial* history on first load — every
    subsequent message arrives through the WebSocket consumer, so the
    HTTP endpoint does not need to do any work on subsequent visits.
    """
    conversation = get_object_or_404(
        chatroom.objects.select_related('product', 'buyer', 'seller'),
        id=chatroom_id,
    )
    # Authorisation: only buyer or seller may view.
    if request.user.id not in (conversation.buyer_id, conversation.seller_id):
        return redirect('home')

    messages = conversation.message.order_by('created_at')
    conversation.other_user = (
        conversation.seller if conversation.buyer_id == request.user.id else conversation.buyer
    )
    qs = (
        chatroom.objects.filter(buyer=request.user) | 
        chatroom.objects.filter(seller=request.user)
    )
    qs = qs.select_related('product', 'buyer', 'seller').order_by('-updated_at')
    rooms = []
    for room in qs:
        room.other_user = room.seller if room.buyer_id == request.user.id else room.buyer
        rooms.append(room)

    return render(request, 'chat_details.html', {
        'conversation': conversation,
        'messages': messages,
        'chatroom': rooms
    })


@login_required
def chat_history(request, chatroom_id):
    """Paginated JSON history endpoint (used by chat UI "load older").

    Returns a page of messages older than `before_id` (if given) or the
    oldest page when requested without a cursor. The consumer itself
    never fetches history — only this endpoint is hit for backfill.
    """
    conversation = get_object_or_404(chatroom, id=chatroom_id)
    if request.user.id not in (conversation.buyer_id, conversation.seller_id):
        return redirect('home')

    qs = conversation.message.order_by('-created_at')
    before_id = request.GET.get('before_id')
    if before_id:
        qs = qs.filter(id__lt=int(before_id))

    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get('page', 1))
    items = [{
        'id': m.id,
        'message': m.message,
        'sender': m.sender.username,
        'sender_id': m.sender_id,
        'created_at': m.created_at.isoformat(),
    } for m in page]

    return render(
        request,
        'partials/_message_batch.html',
        {'messages': list(reversed(items)), 'me_id': request.user.id},
    )