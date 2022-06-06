from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

from http import HTTPStatus
from ..models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user2 = User.objects.create_user(username='NotAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_guest_url_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        url_names = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.post.author.username}/',
            f'/posts/{self.post.id}/']
        for url in url_names:
            with self.subTest():
                response = self.guest_client.get(url,)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_edit_url_exists_at_desired_location(self):
        """Страницы  доступны авторизованному пользователю."""
        url_names = {
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
            f'/posts/{self.post.id}/comment/': HTTPStatus.FOUND}
        for template, status in url_names.items():
            with self.subTest():
                response = self.authorized_client.get(template)
                self.assertEqual(response.status_code, status)

    def test_edit_url_exists_at_desired_location(self):
        """Страница /edit/ доступна только автору."""
        self.authorized_client2.force_login(self.user2)
        response = self.authorized_client2.get(f'/posts/{self.post.id}/edit/',)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_url_redirect_anonymous_on_admin_login(self):
        """Страницы перенаправляют анонимного пользователя
        на страницу логина.
        """
        url_names = [
            '/create/',
            f'/posts/{self.post.id}/edit/']
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html', }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_404_url(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
