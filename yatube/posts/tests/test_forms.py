import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings


from ..models import Group, Post, Comment
from ..forms import PostForm
from http import HTTPStatus


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создаёт новую запись"""
        form_data = {
            'text': 'Тестовый текст тестового поста',
            'group': self.group.id,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Post.objects.order_by('-pub_date').filter(
            pk=1,
            author=self.user,
            text='Тестовый текст тестового поста',
            group=self.group.id).exists())

    def test_edit_post(self):
        """Валидная форма редактирует существующую запись"""
        post = Post.objects.create(

            author=self.user,
            group=self.group
        )
        group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        form_data = {
            'text': 'Изменённый текст тестового поста',
            'group': group2.id
        }

        self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            post.pk}), data=form_data, follow=True)

        edit_post = Post.objects.get(pk=post.pk)
        self.assertEqual(
            edit_post.text, 'Изменённый текст тестового поста')
        self.assertEqual(
            edit_post.group.id, group2.id)
        self.assertEqual(
            edit_post.author, self.user)

    def test_add_comment(self):
        post = Post.objects.create(

            author=self.user,
            group=self.group
        )

        form_data = {
            'text': 'Тестовый комментарий',
        }
        comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': post.pk}),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Comment.objects.order_by('-created').filter(
            pk=1,
            author=self.user,
            text='Тестовый комментарий',).exists())


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImagePostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создаёт новую запись"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')
        form_data = {
            'text': 'Тестовый текст тестового поста',
            'group': self.group.id,
            'image': uploaded
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Post.objects.order_by('-pub_date').filter(
            pk=1,
            author=self.user,
            text='Тестовый текст тестового поста',
            group=self.group.id,).exists())
