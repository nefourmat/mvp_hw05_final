from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .settings import PAGINATOR_COUNT


def page_view(request, post_list):
    paginator = Paginator(post_list, PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    page = page_view(request, Post.objects.all())
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page = page_view(request, group.posts.all())
    context = {'group': group, 'page': page}
    return render(request, 'group.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (
        request.user.is_authenticated
        and author != request.user
        and Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    )
    page = page_view(request, author.posts.all())
    context = {'author': author, 'page': page, 'following': following}
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    following = (
        request.user.is_authenticated
        and post.author != request.user
        and Follow.objects.filter(
            user=request.user,
            author=post.author
        ).exists()
    )
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
        'author': post.author,
        'following': following
        }
    return render(request, 'post.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'new_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('post', username, post_id)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'new_post.html', {'form': form, 'post': post})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comments = form.save(commit=False)
        comments.post = post
        comments.author = request.user
        comments.save()
        return redirect('post', username, post_id)
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    """Посты авторов, на которых подписан текущий пользователь"""
    page = page_view(
        request, Post.objects.filter(author__following__user=request.user))
    context = {'page': page, 'user': request.user}
    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    """Возможность подписаться"""
    if request.user.username != username:
        following_author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(
            user=request.user, author=following_author)
    return redirect('follow_index')


@login_required
def profile_unfollow(request, username):
    """Отписка"""
    unfollow = get_object_or_404(
        Follow, user=request.user, author__username=username)
    unfollow.delete()
    return redirect('follow_index')
