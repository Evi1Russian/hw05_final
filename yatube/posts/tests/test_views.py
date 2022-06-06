import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models import Follow, Group, Post
from ..forms import PostForm
from ..views import AMOUNT_CONST


User = get_user_model()

TEST_CONST: int = AMOUNT_CONST + 3

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
            image='tasks/small.gif'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile',
                    kwargs={'username':
                            self.post.author.username}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            self.group.slug}): 'posts/group_list.html', }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_context(self, response):
        response_post = response.context.get('page_obj')[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_group, self.group)
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_image, self.post.image)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_context(response)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug':
                                                      self.group.slug}))
        response_group = response.context.get('group').slug
        self.assertEqual(response_group, self.group.slug)
        self.check_context(response)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.id}))
        response_post = response.context.get('post')
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text

        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_group, self.group)
        self.assertEqual(post_text, self.post.text)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={
                    'username':
                    self.post.author.username}
            ))
        response_author = response.context.get('author').username
        self.assertEqual(response_author, self.post.author.username)
        self.check_context(response)

    def test_create_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context.get('form')
        is_edit = response.context.get('is_edit')
        self.assertEqual(is_edit, None)
        self.assertIsInstance(form, PostForm)

    def test_edit_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id':
                                                              self.post.id}))
        form = response.context.get('form')
        response_post = response.context.get('post')
        post_author = response_post.author
        post_text = response_post.text
        is_edit = response.context.get('is_edit')
        self.assertEqual(is_edit, True)
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_text, self.post.text)
        self.assertIsInstance(form, PostForm)

    def test_new_post_is_not_in_wrong_group_list(self):
        """Проверка, что пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug':
                                                self.group_2.slug}))
        self.assertEqual(len(response.context.get('page_obj').object_list), 0)

    # def test_images_context(self):


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа1',
            slug='testslug1',
            description='Тестовое описание1',
        )

        obj = (Post(author=cls.user,
                    text=f'Test {i}',
                    group=cls.group, ) for i in range(TEST_CONST))
        cls.posts = Post.objects.bulk_create(obj)
        for cls.post in cls.posts:
            return cls.post

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        url_names = [
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username':
                            self.post.author.username}),
            reverse('posts:group_list',
                    kwargs={'slug':
                            self.group.slug}), ]
        for url in url_names:
            with self.subTest():
                response = self.client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 AMOUNT_CONST)

    def test_second_page_contains_three_records(self):
        url_names = [
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username':
                            self.post.author.username}),
            reverse('posts:group_list',
                    kwargs={'slug':
                            self.group.slug}), ]
        for url in url_names:
            with self.subTest():
                response = self.client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 TEST_CONST - AMOUNT_CONST)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='Alpha')
        cls.user_2 = User.objects.create_user(username='Beta')
        cls.user_3 = User.objects.create_user(username='Gamma')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post1 = Post.objects.create(
            author=cls.user_1,
            text='Тестовая пост',
            group=cls.group
        )
        cls.post2 = Post.objects.create(
            author=cls.user_2,
            text='Тестовая пост',
            group=cls.group
        )
        cls.post3 = Post.objects.create(
            author=cls.user_3,
            text='Тестовая пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)

    def test_authorized_can_follow_and_unfollow(self):
        count_follow_before_follow = Follow.objects.count()
        response = self.authorized_client.get(reverse(
            'posts:profile_follow', args={f'{self.user_2.username}'}))
        count_follow_after_follow = Follow.objects.count()
        self.assertRedirects(response, '/follow/')
        self.assertEqual(
            count_follow_after_follow, count_follow_before_follow + 1)

        response = self.authorized_client.get(reverse(
            'posts:profile_unfollow', args={f'{self.user_2.username}'}))
        self.assertRedirects(
            response, '/follow/')
        self.assertEqual(
            count_follow_after_follow - 1, count_follow_before_follow)

    def test_post_in_follow_and_not_in_unfollow(self):
        response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        count_before_follow = len(response.context.get('page_obj'))
        Follow.objects.get_or_create(user=self.user_1, author=self.user_2)
        response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        count_after_follow = len(response.context.get('page_obj'))
        self.assertEqual(count_before_follow + 1, count_after_follow)

        self.authorized_client.force_login(self.user_3)
        response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        count_posts_in_unfollow_user = len(response.context.get('page_obj'))
        self.assertEqual(count_posts_in_unfollow_user, 0)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        Post.objects.create(
            author=self.user,
            text='Тестовая пост',
            group=self.group
        )
        response = self.authorized_client.get(reverse('posts:index'))
        posts_count = Post.objects.count()
        Post.objects.create(
            author=self.user,
            text='Тестовая пост',
            group=self.group)
        self.assertEqual(len(response.context.get('page_obj')), posts_count)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj')),
                         posts_count + 1)

