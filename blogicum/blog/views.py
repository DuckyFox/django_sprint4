from django.contrib.auth import get_user_model
from datetime import datetime as dt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.db.models import Count
from django.core.exceptions import PermissionDenied
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from django.utils import timezone

from blog.models import Post, Category, Comment
from .forms import PostForm, CommentForm, ProfileEditForm

PAGES_ON_POST = 10
User = get_user_model()


class PostMixin:
    model = Post
    template_name = 'blog/postadd.html'


class IndexListView(ListView):
    model = Post
    ordering = 'id'
    paginate_by = PAGES_ON_POST
    template_name = 'blog/index.html'

    def suitable_posts(self):
        return Post.objects.select_related(
                 'category', 'location', 'author').filter(
                 is_published=True,
                 category__is_published=True,
                 pub_date__lte=dt.now()
                 ).order_by('pub_date').annotate(comment_count=Count('comment'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_count'] = self.suitable_posts().count()
        return context

    def get_queryset(self):
        return self.suitable_posts()


class PostCreateView(PostMixin, LoginRequiredMixin, CreateView):
    form_class = PostForm
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        form.instance.author = self.request.user
        post = form.save(commit=False)
        post.save()
        return super().form_valid(form)


class PostUpdateView(PostMixin, LoginRequiredMixin, UpdateView):
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', pk=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['post_id']})


class PostDeleteView(PostMixin, LoginRequiredMixin, DeleteView):
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy("blog:profile",
                            kwargs={"username": self.request.user})


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model.objects.select_related('location', 'author', 'category')
            .filter(pub_date__lte=timezone.now(),
                    is_published=True,
                    category__is_published=True), pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comment.select_related('author')
        return context


class CategoryPostsListView(ListView):
    model = Post
    paginate_by = PAGES_ON_POST
    template_name = 'blog/category.html'

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Category,
                          slug=kwargs['category_slug'],
                          is_published=True)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )

        return (category.posts.select_related('location', 'author', 'category')
                .filter(is_published=True, pub_date__lte=timezone.now())
                .order_by("pub_date"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = \
            get_object_or_404(Category,
                              slug=self.kwargs['category_slug'])
        return context


class ProfileListView(ListView):
    model = Post
    paginate_by = PAGES_ON_POST
    template_name = 'blog/profile.html'

    def get_queryset(self):
        return (
            self.model.objects.select_related('author')
            .filter(author__username=self.kwargs['username'])
            .annotate(comment_count=Count("comment"))
            .order_by("-pub_date"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username'])
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/user.html'
    form_class = ProfileEditForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy("blog:profile", args=[self.request.user])


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    post_obj = None

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post,
                                          pk=kwargs['post_id'],
                                          is_published=True)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("blog:post_detail",
                            kwargs={'pk': self.kwargs['post_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()
        return context


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['post_id']})

    def get_object(self):
        comment = get_object_or_404(Comment, pk=self.kwargs.get('comment_pk'))
        return comment

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_pk'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_pk'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['post_id']})

    def get_object(self):
        comment = get_object_or_404(Comment, pk=self.kwargs.get('comment_pk'))
        return comment
