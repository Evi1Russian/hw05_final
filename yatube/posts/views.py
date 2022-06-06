from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm

from .models import Post, Group, User, Follow  # Comment

AMOUNT_CONST: int = 10


def paginator(post_list):
    return Paginator(post_list, AMOUNT_CONST)


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related(
        'group', 'author').all().order_by(
        '-pub_date')
    page_number = request.GET.get('page')
    page_obj = paginator(post_list).get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_list(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.select_related(
        'group').filter(group=group).order_by(
        '-pub_date')
    page_number = request.GET.get('page')
    page_obj = paginator(post_list).get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    page_number = request.GET.get('page')
    post_list = author.posts.select_related(
        'group', 'author').order_by(
        '-pub_date')
    page_obj = paginator(post_list).get_page(page_number)
    if request.user.is_authenticated:
        following = Follow.objects.filter(author=author,
                                          user=request.user).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
        'post_list': post_list,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()

    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    if form.is_valid():
        post_create = form.save(commit=False)
        post_create.author = request.user
        post_create.save()
        return redirect('posts:profile', username=request.user)
    form = PostForm()
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(id=post_id)
    is_edit = True
    template = 'posts/create_post.html'
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        instance=post,
        data=request.POST or None,
        files=request.FILES or None,)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {'form': form, 'post': post, 'is_edit': is_edit}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = []
    user = request.user
    follows = Follow.objects.filter(user=user)
    if len(follows) > 0:
        for follow in follows:
            posts.extend(Post.objects.filter(author=follow.author))
    page_number = request.GET.get('page')
    page_obj = paginator(posts).get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    follow_user = get_object_or_404(User, username=request.user)
    if follow_user != author:
        Follow.objects.get_or_create(
            author=author,
            user=follow_user,
        )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    follow_user = get_object_or_404(User, username=request.user)
    if follow_user != author:
        Follow.objects.get(
            author=author,
            user=follow_user,
        ).delete()
    return redirect('posts:follow_index')
