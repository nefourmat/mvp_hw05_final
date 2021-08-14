from django.test.testcases import TestCase
from django.urls import reverse
from posts.models import Post, User

TEST_USERNAME = 'mike'
TEST_SLUG = 'test-slug'
POST_TEXT = 'Проверка создание поста'


class RoutesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(TEST_USERNAME)
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.user)

    def test(self):
        route_names = [
            ['index', [], '/'],
            ['new_post', [], '/new/'],
            ['follow_index', [], '/follow/'],
            ['group_posts', [TEST_SLUG], f'/group/{TEST_SLUG}/'],
            ['profile', [TEST_USERNAME], f'/{TEST_USERNAME}/'],
            ['post', [TEST_USERNAME, self.post.id],
             f'/{TEST_USERNAME}/{self.post.id}/'],
            ['post_edit', [TEST_USERNAME, self.post.id],
             f'/{TEST_USERNAME}/{self.post.id}/edit/'],
            ['profile_follow', [TEST_USERNAME], f'/{TEST_USERNAME}/follow/'],
            ['profile_unfollow', [TEST_USERNAME],
             f'/{TEST_USERNAME}/unfollow/']
        ]
        for name, parameters, url in route_names:
            self.assertEqual(reverse(name, args=parameters), url)
