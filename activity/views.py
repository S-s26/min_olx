from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import UserActivity


@login_required
def my_activity(request):
    """The signed-in user's own activity timeline."""
    qs = UserActivity.objects.filter(user=request.user).order_by('-created_at')[:200]
    return render(request, 'my_activity.html', {'activities': qs})