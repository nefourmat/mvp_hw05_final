from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User
from posts.settings import PAGINATOR_COUNT

TEST_USERNAME = 'mike'
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
REMAINDER = 1


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(TEST_USERNAME)
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
            author=cls.user)
        cls.POST_URL = reverse('post', kwargs={
            'username': cls.user.username,
            'post_id': cls.post.id})

    def setUp(self):
        """Создаем пользователя"""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_context(self):
        """Проверка контекста"""
        cache.clear()
        urls = {
            HOMEPAGE_URL: 'page',
            GROUP_URL: 'page',
            PROFILE_URL: 'page',
            self.POST_URL: 'post'
        }
        for url, key in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                if key == 'post':
                    post = response.context[key]
                else:
                    self.assertEqual(len(response.context[key]), 1)
                    post = response.context[key][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)

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
