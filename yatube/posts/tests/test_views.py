import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User, Follow
from posts.settings import PAGINATOR_COUNT

TEST_USERNAME = 'mike'
TEST_USERNAME_2 = 'jackson'
TEST_TEXT = 'test-text'
TEST_SLUG = 'test-slug'
TEST_TITLE = 'test-title'
TEST_TITLE_2 = 'test-another'
TEST_SLUG_2 = 'test-slug_2'
TEST_DESCRIPTION_2 = 'test-description_2'
TEST_DESCRIPTION = 'test-description'
HOMEPAGE_URL = reverse('index')
GROUP_POST_URL = reverse('group_posts', kwargs={'slug': TEST_SLUG})
PROFILE_URL = reverse('profile', kwargs={'username': TEST_USERNAME})
GROUP_URL = reverse('group_posts', kwargs={'slug': TEST_SLUG})
ANOTHER_URL = reverse('group_posts', kwargs={'slug': TEST_SLUG_2})
FOLLOW_INDEX = reverse('follow_index')
REMAINDER = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
PICTURE = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
           b'\x01\x00\x80\x00\x00\x00\x00\x00'
           b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
           b'\x00\x00\x00\x2C\x00\x00\x00\x00'
           b'\x02\x00\x01\x00\x00\x02\x02\x0C'
           b'\x0A\x00\x3B')
UPLOADED = SimpleUploadedFile(
           name='small.gif',
           content=PICTURE,
           content_type='image/gif')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(TEST_USERNAME)
        cls.user_2 = User.objects.create_user(TEST_USERNAME_2)
        cls.group = Group.objects.create(
            title=TEST_TITLE,
            slug=TEST_SLUG,
            description=TEST_DESCRIPTION)
        cls.another_group = Group.objects.create(
            title=TEST_TITLE_2,
            slug=TEST_SLUG_2,
            description=TEST_DESCRIPTION_2)
        cls.post = Post.objects.create(
            text=TEST_TEXT,
            group=cls.group,
            author=cls.user,
            image=UPLOADED)
        cls.follow = Follow.objects.get_or_create(
            author=cls.user,
            user=cls.user_2).count()
        cls.POST_URL = reverse('post', kwargs={
            'username': cls.user.username,
            'post_id': cls.post.id})
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_context(self):
        """Проверка контекста"""
        urls = {
            HOMEPAGE_URL: 'page',
            GROUP_URL: 'page',
            PROFILE_URL: 'page',
            self.POST_URL: 'post',
            FOLLOW_INDEX: 'page',
        }
        for url, key in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if key == 'post':
                    post = response.context[key]
                else:
                    self.assertEqual(len(response.context[key]), 1)
                    post = response.context[key][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)

    def test_another_group(self):
        """Пост находиться в нужной группе"""
        response = self.authorized_client.get(ANOTHER_URL)
        self.assertNotIn(self.post, response.context['page'])

    def test_context_profile(self):
        """Пост находиться в профиле"""
        response = self.authorized_client.get(PROFILE_URL)
        context_group = response.context['author']
        self.assertEqual(self.user.username, context_group.username)

    def test_context_group(self):
        """Пост в нужной группе"""
        response = self.authorized_client.get(GROUP_URL)
        context_group = response.context['group']
        self.assertEqual(self.group.title, context_group.title)
        self.assertEqual(self.group.slug, context_group.slug)
        self.assertEqual(self.group.description,
                         context_group.description)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(TEST_USERNAME)
        for posts in range(PAGINATOR_COUNT + REMAINDER):
            cls.post = Post.objects.create(
                text=TEST_TEXT,
                author=cls.user)

    def setUp(self):
        self.guest_client = Client()

    def test_paginator_homepage(self):
        """"Paginator выполняет свои действия. 1-ая страница"""
        cache.clear()
        response = self.guest_client.get(HOMEPAGE_URL)
        self.assertEqual(len(
            response.context['page']), PAGINATOR_COUNT)

    def test_paginator_homepage_2(self):
        """2-ая страница"""
        response = self.guest_client.get(HOMEPAGE_URL + '?page=2')
        result = len(response.context.get('page'))
        self.assertEqual(result, REMAINDER)
