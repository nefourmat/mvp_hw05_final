import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User, Comment

HOMEPAGE_URL = reverse('index')
NEW_POST_URL = reverse('new_post')
LOGIN_URL = reverse('login') + '?next='
TEST_USERNAME = 'mike'
POST_TEXT = 'Проверка создание поста'
FORM_TEXT = 'Текст из формы'
COMMENT_TEXT = 'коммент'
NOT_AUTH_USER = 'пользователь не авторизован'
TEST_TITLE = 'test-title'
TEST_SLUG = 'test-slug'
TEST_DESCRIPTION = 'test-description'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
PICTURE = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
           b'\x01\x00\x80\x00\x00\x00\x00\x00'
           b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
           b'\x00\x00\x00\x2C\x00\x00\x00\x00'
           b'\x02\x00\x01\x00\x00\x02\x02\x0C'
           b'\x0A\x00\x3B')
UPLOADED = SimpleUploadedFile(
    name='small.gif', content=PICTURE, content_type='image/gif')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateForm(TestCase):
    """Форма для создания поста."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostCreateForm()
        cls.user = User.objects.create_user(TEST_USERNAME)
        cls.gpoup = Group.objects.create(
            title=TEST_TITLE,
            slug=TEST_SLUG,
            description=TEST_DESCRIPTION)
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.user,
            group=cls.gpoup,
            image=UPLOADED)
        cls.POST_EDIT_URL = reverse('post_edit', kwargs={
            'username': cls.user.username,
            'post_id': cls.post.id})
        cls.POST_URL = reverse('post', kwargs={
            'username': cls.user.username,
            'post_id': cls.post.id})
        cls.COMMENT_URL = reverse('add_comment', kwargs={
            'username': cls.user.username,
            'post_id': cls.post.id})
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_unauth_user_cant_publish_pos(self):
        """Попытка создания поста не автор-ым пользователем"""
        keys_posts = set(Post.objects.values_list('id'))
        form_data = {
            'text': FORM_TEXT,
            'author': self.user}
        response = self.guest_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            (LOGIN_URL + NEW_POST_URL))
        self.assertEqual(set(Post.objects.values_list('id')), keys_posts)

    def test_auth_user_can_publish_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': FORM_TEXT,
            'group': self.gpoup.id,
            'image': self.post.image}
        response = self.authorized_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, HOMEPAGE_URL)
        new_posts = [
            post for post in response.context['page'] if post != self.post]
        self.assertEqual(len(new_posts), 1)
        new_post = new_posts[0]
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(self.post.image, form_data['image'].name)

    def test_new_post(self):
        """Шаблон редактирования/создания поста с нужным context"""
        urls = [NEW_POST_URL, self.POST_EDIT_URL]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField
                }
                for value, context_form_field in form_fields.items():
                    with self.subTest(value=value, url=url):
                        post_field = response.context['form'].fields[value]
                        self.assertIsInstance(post_field, context_form_field)

    def test_edit_post(self):
        """Редактирование поста"""
        # не получается работать с константой UPLOADED
        # И меняем название картинки для редактирования
        uploaded = SimpleUploadedFile(
            name='small_edited.gif', content=PICTURE, content_type='image/gif')
        posts_count = Post.objects.count()
        form_data = {
            'text': FORM_TEXT,
            'group': self.gpoup.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        post_to_edit = response.context['post']
        self.assertRedirects(response, self.POST_URL)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_to_edit.id, self.post.id)
        self.assertEqual(post_to_edit.text, form_data['text'])
        self.assertEqual(post_to_edit.group.id, form_data['group'])
        self.assertEqual(post_to_edit.author, self.post.author)
        self.assertEqual(post_to_edit.image, 'posts/small_edited.gif')

    def test_create_new_comment(self):
        """Комментарий"""
        comment_count = Comment.objects.count()
        form_data = {
            "text": COMMENT_TEXT,
        }
        response = self.authorized_client.post(
            self.COMMENT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_URL)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(len(response.context['comments']), 1)
        added_comment = response.context['comments'][0]
        self.assertEqual(added_comment.post, self.post)
        self.assertEqual(added_comment.author, self.user)
        self.assertEqual(added_comment.text, form_data['text'])

    def test_update_post_guest(self):
        """Редактирование гостем """
        form_data = {
            'text': FORM_TEXT,
            'group': self.gpoup.id,
            'picture': self.post.image
        }
        response = self.guest_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, LOGIN_URL + self.POST_EDIT_URL)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
