from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .settings import PAGINATOR_COUNT


#@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'posts': post_list})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'group': group, 'posts': posts, 'page': page}
    return render(request, 'group.html', context)


def profile(request, username):
    following = request.user.is_authenticated and Follow.objects.filter(user = request.user, author__username=username).exists()
    author = get_object_or_404(User, username=username)
    post = author.posts.all()
    paginator = Paginator(post, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'author': author, 'page': page, 'following': following}
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = Comment.objects.all()
    form = CommentForm(request.POST or None)
    context = {'post': post, 'form': form, 'comments': comments}
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
    return render(request, "comments.html", {'form': form})


@login_required
def follow_index(request):
    """Посты авторов, на которых подписан текущий пользователь"""
    # информация о текущем пользователе доступна в переменной request.user
    user = request.user
    #post_list = user.following.all()
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'post_list': post_list, 'page': page, 'user': user}
    return render(request, "follow.html", context)

@login_required
def profile_follow(request, username):
    """Возможность подписаться"""
    if request.user.username != username:
        following_author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user = request.user, author = following_author)
    return redirect('follow_index')


@login_required
def profile_unfollow(request, username):
    """Отписка"""
    unfollow = Follow.objects.filter(user = request.user, author__username=username)
    unfollow.delete()
    return redirect('follow_index')