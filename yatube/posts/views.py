from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import get_ten_posts_per_page


@cache_page(20, key_prefix='index_page')
def index(request):
    """Вью-функция главной страницы"""
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group', 'author')
    context = {
        'page_obj': get_ten_posts_per_page(request, post_list),
    }

    return render(request, template, context)


def group_posts(request, slug):
    """Вью-функция страниц сообществ"""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group', 'author')
    context = {
        'group': group,
        'page_obj': get_ten_posts_per_page(request, post_list),
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Вью-функция просмотра профиля пользователя с публикациями"""
    author = get_object_or_404(
        User.objects.select_related(),
        username=username,
    )
    post_list = author.posts.all()
    if request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists():
        following = True
    else:
        following = False
    context = {
        'page_obj': get_ten_posts_per_page(request, post_list),
        'author': author,
        'following': following,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Вью-функция просмотра отдельной публикации"""
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    form = CommentForm(request.POST or None)
    comments = post.comments.select_related('post', 'author')
    if request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists():
        following = True
    else:
        following = False
    context = {
        'post': post,
        'form': form,
        'comments': comments,
        'author': author,
        'following': following,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Вью-функция страницы создания публикации"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:profile', username=post.author)

    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Вью-функция изменения публикации"""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:post_detail', post_id=post_id)

    return render(
        request,
        'posts/create_post.html',
        {'is_edit': True, 'form': form, 'post': post},
    )


@login_required
def add_comment(request, post_id):
    """Вью-функция добавления комментария"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Вью-функция страницы с постами на подписки"""
    user = request.user
    posts_list = Post.objects.filter(author__following__user=user)
    context = {
        'user': user,
        'page_obj': get_ten_posts_per_page(request, posts_list),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.filter(username=username).get()
    if request.user == author or Follow.objects.filter(
        user=request.user,
        author=author,
    ).exists():
        return redirect('posts:profile', username=username)
    else:
        Follow.objects.create(user=request.user, author=author)
        return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = User.objects.filter(username=username).get()
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')