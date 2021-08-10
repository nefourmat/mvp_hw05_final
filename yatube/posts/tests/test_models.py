from django.test import TestCase

from posts.models import Group, Post, User


TEST_USERNAME = 'mike'


class PostModelTest(TestCase):
    """Тестируем класс Post"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(TEST_USERNAME)
        cls.post = Post.objects.create(
            text='Проверка создание поста',
            author=cls.user)

    def test__str__(self):
        """Тестируем метод __str__ для класса Post"""
        post = PostModelTest.post
        expected_text = post.text
        self.assertEqual(expected_text, str(post),
                         'Метод __str__ работает неправильно'
                         )


class GroupModelTest(TestCase):
    """Тестируем класс Group"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Проверка создание поста')

    def test__str__(self):
        """Тестируем метод __str__ для класса Group"""
        group = GroupModelTest.group
        expected_title = group.title
        self.assertEqual(expected_title, str(group),
                         'Метод создния группы не корректен'
                         )
