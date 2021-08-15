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
TEST_USERNAME_3 = 'arnold'
TEST_TEXT = 'test-text'
CASH_TEXT = 'проверяем кэш'
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
PROFILE_FOLLOW = reverse(
    'profile_follow', kwargs={'username': TEST_USERNAME})
PROFILE_UNFOLLOW = reverse(
    'profile_unfollow', kwargs={'username': TEST_USERNAME})
NEW_POST_URL = reverse('new_post')
REMAINDER = 1
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
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(TEST_USERNAME)
        cls.user_2 = User.objects.create_user(TEST_USERNAME_2)
        cls.user_3 = User.objects.create_user(TEST_USERNAME_3)
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
        cls.POST_URL = reverse('post', kwargs={
            'username': cls.user.username,
            'post_id': cls.post.id})
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        #  второй клиент
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)
        #  фолловер
        cls.authorized_follower = Client()
        cls.authorized_follower.force_login(cls.user_3)

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
        }
        for url, key in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client_2.get(url)
                if key == 'post':
                    post = response.context[key]
                else:
                    self.assertEqual(len(response.context[key]), 1)
                    post = response.context[key][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)

    def test_follow(self):
        response_1 = self.authorized_client_2.get(FOLLOW_INDEX)
        page_object_1 = response_1.context['page'].object_list
        self.assertEqual(len(page_object_1), 0)  # исправить
        self.authorized_client_2.get(PROFILE_FOLLOW)
        follows = Follow.objects.filter(
            user=self.user_2, author=self.user).count()
        self.assertEqual(follows, 1)
        self.authorized_client_2.get(PROFILE_UNFOLLOW)
        follows = Follow.objects.filter(
            user=self.user_2, author=self.user).count()
        self.assertNotEqual(follows, 1)

    def test_another_group(self):
        response = self.authorized_client.get(ANOTHER_URL)
        self.assertNotIn(self.post, response.context['page'])

    def test_context_group_author(self):
        urls = {
            PROFILE_URL: 'author',
            GROUP_URL: 'group'
        }
        for url, key in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                context = response.context[key]
                if key == 'author':
                    self.assertEqual(self.user.username, context.username)
                else:
                    self.assertEqual(self.group.title, context.title)
                    self.assertEqual(self.group.slug, context.slug)
                    self.assertEqual(self.group.description,
                                     context.description)

    def test_new_post_check_at_followers(self):
        self.authorized_follower.get(PROFILE_FOLLOW)
        form_data = {
            'text': TEST_TEXT,
            'author': self.user,
        }
        self.authorized_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        response = self.authorized_follower.get(FOLLOW_INDEX)
        self.assertContains(response, form_data['text'])
        response = self.authorized_client_2.get(FOLLOW_INDEX)
        self.assertNotContains(response, form_data['text'])

    def test_index_cache_check(self):
        response = self.authorized_client.get(HOMEPAGE_URL)
        post = Post.objects.create(
            text=CASH_TEXT,
            author=self.user
        )
        page = response.content
        self.assertEqual(page, response.content)
        post.delete()
        response = self.client.get(HOMEPAGE_URL)
        cache.clear()
        self.assertNotEqual(response, response.content)


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
