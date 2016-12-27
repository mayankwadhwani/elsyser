from django.contrib.auth.models import User, Group

from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token

from datetime import datetime, timedelta

from .models import Class, Student, Subject, Exam, News, Homework, Comment
from .serializers import (
    StudentProfileSerializer,
    NewsSerializer,
    CommentSerializer,
    ExamSerializer,
    HomeworkSerializer
)


class RegisterViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.view_name = 'students:register'

        self.test_data = {
            'user': {
                'username': 'tester',
                'first_name': 'test',
                'last_name': 'user',
                'email': 'tester@gmail.com',
                'password': 'testerpassword123456',
            },
            'clazz': {
                'number': 10,
                'letter': 'A',
            }
        }


    def test_registration_with_empty_email(self):
        self.test_data['user']['email'] = ''

        request = self.client.post(
            reverse(self.view_name), self.test_data, format='json'
        )

        self.assertEqual(
            request.data['user']['email'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_registration_with_invalid_email(self):
        self.test_data['user']['email'] = 'tester'

        request = self.client.post(
            reverse(self.view_name), self.test_data, format='json'
        )

        self.assertEqual(
            request.data['user']['email'], ['Enter a valid email address.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_registration_with_empty_password(self):
        self.test_data['user']['password'] = ''

        request = self.client.post(
            reverse(self.view_name), self.test_data, format='json'
        )

        self.assertEqual(
            request.data['user']['password'], ['Password cannot be empty.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_registration_with_too_short_password(self):
        self.test_data['user']['password'] = 'test'

        request = self.client.post(
            reverse(self.view_name), self.test_data, format='json'
        )

        self.assertEqual(
            request.data['user']['password'], ['Password too short.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_registration_with_invalid_clazz(self):
        self.test_data['clazz']['number'] = 0

        request = self.client.post(
            reverse(self.view_name), self.test_data, format='json'
        )

        self.assertEqual(
            request.data['clazz']['number'], ['"0" is not a valid choice.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_registration_with_valid_data(self):
        request = self.client.post(
            reverse(self.view_name), self.test_data, format='json'
        )

        user_data = request.data['user']
        user = User.objects.get(**user_data)

        self.assertEqual(self.test_data['user']['username'], user.username)
        self.assertEqual(self.test_data['user']['first_name'], user.first_name)
        self.assertEqual(self.test_data['user']['last_name'], user.last_name)
        self.assertEqual(self.test_data['user']['email'], user.email)
        self.assertIsNotNone(
            Token.objects.get(user__username=user_data['username'])
        )
        self.assertEqual(request.status_code, status.HTTP_201_CREATED)


class LoginViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.view_name = 'students:login'

        self.user_data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': ''.join(map(str, range(1, 10)))
        }
        self.user = User.objects.create_user(**self.user_data)
        self.token = Token.objects.create(user=self.user)
        self.post_data = {
            'email_or_username': '',
            'password': self.user_data['password'],
        }


    def test_login_with_blank_email_or_username(self):
        request = self.client.post(reverse(self.view_name), self.post_data)

        self.assertEqual(
            request.data['email_or_username'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_login_with_blank_password(self):
        self.post_data['email_or_username'] = self.user.email
        self.post_data['password'] = ''

        request = self.client.post(reverse(self.view_name), self.post_data)

        self.assertEqual(
            request.data['password'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_login_with_invalid_email_or_username(self):
        self.post_data['email_or_username'] = 'invalid'

        request = self.client.post(reverse(self.view_name), self.post_data)

        self.assertEqual(
            request.data['non_field_errors'],
            ['Unable to log in with provided credentials.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_login_with_invalid_password(self):
        self.post_data['email_or_username'] = self.user.email
        self.post_data['password'] = 'invalidpassword'

        request = self.client.post(reverse(self.view_name), self.post_data)

        self.assertEqual(
            request.data['non_field_errors'],
            ['Unable to log in with provided credentials.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_login_with_valid_email_and_password(self):
        self.post_data['email_or_username'] = self.user.email

        request = self.client.post(reverse(self.view_name), self.post_data)

        self.assertEqual(self.token.key, request.data['token'])
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_login_with_valid_username_and_password(self):
        self.post_data['email_or_username'] = self.user.username

        request = self.client.post(reverse(self.view_name), self.post_data)

        self.assertEqual(self.token.key, request.data['token'])
        self.assertEqual(request.status_code, status.HTTP_200_OK)


class ProfileViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.view_name = 'students:profile'

        self.user = User.objects.create(
            username='tester',
            first_name='test',
            last_name='user',
            email='tester@gmail.com',
            password='pass'
        )
        self.clazz = Class.objects.create(number=10, letter='A')
        self.student = Student.objects.create(
            user=self.user, clazz=self.clazz, info='I am the lord of the rings.'
        )


    def test_profile_with_anonymous_user(self):
        request = self.client.get(reverse(self.view_name))

        self.assertEqual(
            request.data['detail'],
            'Authentication credentials were not provided.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_profile_with_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.get(reverse(self.view_name))

        self.assertEqual(
            self.student.user.username, request.data['user']['username']
        )
        self.assertEqual(
            self.student.clazz.number, request.data['clazz']['number']
        )
        self.assertEqual(
            self.student.clazz.letter, request.data['clazz']['letter']
        )
        self.assertEqual(self.student.info, request.data['info'])
        self.assertNotIn('password', request.data['user'])
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_profile_update_with_invalid_username(self):
        self.client.force_authenticate(user=self.user)
        self.student.user.username = ''
        put_data = StudentProfileSerializer(self.student).data

        request = self.client.put(
            reverse(self.view_name), put_data, format='json'
        )

        self.assertEqual(
            request.data['user']['username'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_profile_update_with_invalid_first_name(self):
        self.client.force_authenticate(user=self.user)
        self.student.user.first_name = ''
        put_data = StudentProfileSerializer(self.student).data

        request = self.client.put(
            reverse(self.view_name), put_data, format='json'
        )

        self.assertEqual(
            request.data['user']['first_name'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_profile_update_with_invalid_last_name(self):
        self.client.force_authenticate(user=self.user)
        self.student.user.last_name = ''
        put_data = StudentProfileSerializer(self.student).data

        request = self.client.put(
            reverse(self.view_name), put_data, format='json'
        )

        self.assertEqual(
            request.data['user']['last_name'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_profile_update_with_valid_data(self):
        self.client.force_authenticate(user=self.user)
        self.student.user.username = 'MyNewUsername'
        self.student.user.first_name = 'John'
        self.student.user.last_name = 'Travolta'
        put_data = StudentProfileSerializer(self.student).data

        # TODO: Fix view and try to remove this line.
        put_data.pop('profile_image')

        request = self.client.put(
            reverse(self.view_name), put_data, format='json'
        )

        self.assertEqual(request.status_code, status.HTTP_200_OK)


class ExamsViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_view_name = 'students:exams-list'
        self.detail_view_name = 'students:exams-detail'
        self.serializer_class = ExamSerializer

        self.student_user = User.objects.create(username='test', password='pass')
        self.teacher_user = User.objects.create(username='teacher', password='123456')
        self.group = Group.objects.create(name='Teachers')
        self.group.user_set.add(self.teacher_user)
        self.clazz = Class.objects.create(number=10, letter='A')
        self.student = Student.objects.create(user=self.student_user, clazz=self.clazz)
        self.subject = Subject.objects.create(title='Maths')
        self.exam = Exam.objects.create(
            subject=self.subject,
            date=datetime.now().date(),
            clazz=self.clazz,
            topic='Quadratic inequations',
            details='This will be the hardest **** ever!!!',
            author=self.teacher_user
        )


    def test_exams_list_with_anonymous_user(self):
        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(
            request.data['detail'],
            'Authentication credentials were not provided.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_exams_detail_with_anonymous_user(self):
        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id})
        )

        self.assertEqual(
            request.data['detail'],
            'Authentication credentials were not provided.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_exams_with_authenticated_user(self):
        self.client.force_authenticate(user=self.student_user)

        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(
            self.subject.title, request.data[0]['subject']['title']
        )
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_exams_detail_with_authenticated_user(self):
        self.client.force_authenticate(user=self.student_user)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id})
        )

        self.assertIsNotNone(request.data)
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_exams_list_with_expired_date(self):
        self.client.force_authenticate(user=self.student_user)
        self.exam.date -= timedelta(days=5)
        self.exam.save()

        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(request.data, [])
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_exams_detail_with_invalid_id(self):
        self.client.force_authenticate(user=self.student_user)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id + 1})
        )

        self.assertEqual(request.data['detail'], 'Not found.')
        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)


    def test_exams_detail_with_valid_id(self):
        self.client.force_authenticate(user=self.student_user)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id})
        )

        self.assertEqual(request.data['details'], self.exam.details)
        self.assertEqual(request.data['topic'], self.exam.topic)
        self.assertEqual(request.data['subject']['title'], self.subject.title)
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_exams_addition_with_student_account(self):
        self.client.force_authenticate(user=self.student_user)
        self.exam.topic = 'glucimir'
        post_data = self.serializer_class(self.exam).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['detail'],
            'You do not have permission to perform this action.'
        )
        self.assertEqual(request.status_code, status.HTTP_403_FORBIDDEN)


    def test_exams_addition_with_empty_topic(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.exam.topic = ''
        post_data = self.serializer_class(self.exam).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(request.data['topic'], ['This field may not be blank.'])
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_exams_addition_with_too_long_topic(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.exam.topic = 'glucimir' * 20
        post_data = self.serializer_class(self.exam).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['topic'],
            ['Ensure this field has no more than 60 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_exams_addition_with_valid_topic(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.exam.topic = 'glucimir'
        post_data = self.serializer_class(self.exam).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(request.status_code, status.HTTP_201_CREATED)


    def test_exams_update_with_student_account(self):
        self.client.force_authenticate(user=self.student_user)
        self.exam.topic = 'glucimir'
        put_data = self.serializer_class(self.exam).data

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id}),
            put_data,
            format='json'
        )

        self.assertEqual(
            request.data['detail'],
            'You do not have permission to perform this action.'
        )
        self.assertEqual(request.status_code, status.HTTP_403_FORBIDDEN)


    def test_exams_update_with_empty_topic(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.exam.topic = ''
        put_data = self.serializer_class(self.exam).data

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id}),
            put_data,
            format='json'
        )

        self.assertEqual(request.data['topic'], ['This field may not be blank.'])
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_exams_update_with_too_long_topic(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.exam.topic = 'glucimir' * 20
        put_data = self.serializer_class(self.exam).data

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id}),
            put_data,
            format='json'
        )

        self.assertEqual(
            request.data['topic'],
            ['Ensure this field has no more than 60 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_exams_update_with_valid_topic(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.exam.topic = 'glucimir'
        put_data = self.serializer_class(self.exam).data

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id}),
            put_data,
            format='json'
        )

        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_exams_update_of_another_user(self):
        self.client.force_authenticate(user=self.teacher_user)

        new_user = User.objects.create(username='test2', password='pass')
        self.group.user_set.add(new_user)
        self.exam.author = new_user
        self.exam.save()

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id}),
            {'topic': 'HAHAHA I AM ANONYMOUS!'},
            format='json'
        )

        self.assertEqual(
            request.data['message'], 'You can edit only your own exams.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_exams_deletion_of_another_user(self):
        self.client.force_authenticate(user=self.teacher_user)

        new_user = User.objects.create(username='test2', password='pass')
        self.group.user_set.add(new_user)
        self.exam.author = new_user
        self.exam.save()

        request = self.client.delete(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id})
        )

        self.assertEqual(
            request.data['message'], 'You can delete only your own exams.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_exams_deletion(self):
        self.client.force_authenticate(user=self.teacher_user)

        request = self.client.delete(
            reverse(self.detail_view_name, kwargs={'pk': self.exam.id})
        )

        self.assertEqual(
            request.data['message'], 'Exam successfully deleted.'
        )
        self.assertEqual(request.status_code, status.HTTP_200_OK)


class NewsViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_view_name = 'students:news-list'
        self.detail_view_name = 'students:news-detail'

        self.user = User(username='test', email='sisko@gmail.com')
        self.user.set_password('password123')
        self.user.save()

        self.clazz = Class.objects.create(number=10, letter='A')
        self.student = Student.objects.create(user=self.user, clazz=self.clazz)
        self.news = News.objects.create(
            title='test_news',
            content='blablabla',
            author=self.student,
        )
        self.comment = Comment.objects.create(
            news=self.news,
            posted_by=self.student,
            content='This is a very nice platform!'
        )


    def test_news_list_with_anonymous_user(self):
        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(
            request.data['detail'],
            'Authentication credentials were not provided.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_news_detail_with_anonymous_user(self):
        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id})
        )

        self.assertEqual(
            request.data['detail'],
            'Authentication credentials were not provided.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_news_with_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.get(reverse(self.list_view_name))

        self.assertIsNotNone(request.data)
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_news_detail_with_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id})
        )

        self.assertIsNotNone(request.data)
        self.assertEqual(request.status_code, status.HTTP_200_OK)



    def test_news_list_with_teacher_account(self):
        teacher = User.objects.create(username='teacher', password='123456')
        group = Group.objects.create(name='Teachers')
        group.user_set.add(teacher)

        self.client.force_authenticate(user=teacher)

        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(
            request.data['detail'],
            'You do not have permission to perform this action.'
        )
        self.assertEqual(request.status_code, status.HTTP_403_FORBIDDEN)


    def test_news_list_with_same_class(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(request.data[0]['title'], self.news.title)
        self.assertEqual(request.data[0]['content'], self.news.content)
        self.assertEqual(
            request.data[0]['author']['user'], self.user.username
        )
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_news_list_with_different_class(self):
        self.client.force_authenticate(user=self.user)
        self.student.clazz = Class.objects.create(number=11, letter='V')

        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(request.data, [])
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_news_list_addition_with_empty_title(self):
        self.client.force_authenticate(user=self.user)
        self.news.title = ''
        post_data = NewsSerializer(self.news).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['title'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_list_addition_with_too_short_title(self):
        self.client.force_authenticate(user=self.user)
        self.news.title = 'yo'
        post_data = NewsSerializer(self.news).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['title'],
            ['Ensure this field has at least 3 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_list_addition_with_too_long_title(self):
        self.client.force_authenticate(user=self.user)
        self.news.title = 'yo' * 120
        post_data = NewsSerializer(self.news).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['title'],
            ['Ensure this field has no more than 100 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_list_addition_with_empty_content(self):
        self.client.force_authenticate(user=self.user)
        self.news.content = ''
        post_data = NewsSerializer(self.news).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['content'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_list_addition_with_too_short_content(self):
        self.client.force_authenticate(user=self.user)
        self.news.content = 'hey'
        post_data = NewsSerializer(self.news).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['content'],
            ['Ensure this field has at least 5 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_list_addition_with_too_long_content(self):
        self.client.force_authenticate(user=self.user)
        self.news.content = 'Hey Jude!' * 10000
        post_data = NewsSerializer(self.news).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['content'],
            ['Ensure this field has no more than 10000 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_list_addition_with_valid_data(self):
        self.client.force_authenticate(user=self.user)
        self.news.title = 'testNews'
        self.news.content = 'testContent'
        post_data = NewsSerializer(self.news).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(request.data['title'], self.news.title)
        self.assertEqual(request.data['content'], self.news.content)
        self.assertEqual(request.status_code, status.HTTP_201_CREATED)


    def test_news_detail_with_invalid_id(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id + 1})
        )

        self.assertEqual(request.data['detail'], 'Not found.')
        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)


    def test_news_detail_with_valid_id(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id})
        )

        self.assertEqual(request.data['id'], self.news.id)
        self.assertEqual(request.data['title'], self.news.title)
        self.assertEqual(request.data['content'], self.news.content)
        self.assertEqual(request.data['author']['user'], self.user.username)

        comments_data = request.data['comment_set']
        self.assertEqual(comments_data[0]['content'], self.comment.content)
        self.assertEqual(
            comments_data[0]['posted_by']['user'], self.user.username
        )

        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_news_update_of_another_user(self):
        self.client.force_authenticate(user=self.user)

        new_user = User.objects.create(username='test2', password='pass')
        new_student = Student.objects.create(user=new_user, clazz=self.clazz)
        self.news.author = new_student
        self.news.save()

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
            {'title': 'HAHAHA I AM ANONYMOUS!'},
            format='json'
        )

        self.assertEqual(
            request.data['message'], 'You can edit only your own posts.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_news_update_with_empty_title(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
            {'title': ''},
            format='json'
        )

        self.assertEqual(
            request.data['title'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_update_with_too_short_title(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
            {'title': 'yo'},
            format='json'
        )

        self.assertEqual(
            request.data['title'],
            ['Ensure this field has at least 3 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_update_with_too_long_title(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
            {'title': 'yo' * 500},
            format='json'
        )

        self.assertEqual(
            request.data['title'],
            ['Ensure this field has no more than 100 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_update_with_empty_content(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
            {'content': ''},
            format='json'
        )

        self.assertEqual(
            request.data['content'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_update_with_too_short_content(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
            {'content': 'hey!'},
            format='json'
        )

        self.assertEqual(
            request.data['content'],
            ['Ensure this field has at least 5 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_update_with_too_long_content(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
            {'content': 'Hey Jude!' * 10000},
            format='json'
        )

        self.assertEqual(
            request.data['content'],
            ['Ensure this field has no more than 10000 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_news_update_with_valid_data(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
            {'title': 'So far, so good!', 'content': 'So what?'},
            format='json'
        )

        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_news_deletion_of_another_user(self):
        self.client.force_authenticate(user=self.user)

        new_user = User.objects.create(username='test2', password='pass')
        new_student = Student.objects.create(user=new_user, clazz=self.clazz)
        self.news.author = new_student
        self.news.save()

        request = self.client.delete(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id}),
        )

        self.assertEqual(
            request.data['message'], 'You can delete only your own posts.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_news_deletion_with_invalid_id(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.delete(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id + 1})
        )

        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)


    def test_news_deletion_with_valid_id(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.delete(
            reverse(self.detail_view_name, kwargs={'pk': self.news.id})
        )

        self.assertEqual(request.status_code, status.HTTP_200_OK)


class CommentsViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_view_name = 'students:comments-list'
        self.detail_view_name = 'students:comments-detail'

        self.user = User.objects.create(username='test1', password='pass')
        self.clazz = Class.objects.create(number=10, letter='A')
        self.student = Student.objects.create(user=self.user, clazz=self.clazz)
        self.news = News.objects.create(
            title='test_news',
            content='blablabla',
            author=self.student,
        )
        self.comment = Comment.objects.create(
            news=self.news,
            posted_by=self.student,
            content='This is a very nice platform!'
        )


    def test_comment_addition_with_empty_content(self):
        self.client.force_authenticate(user=self.user)
        self.comment.content = ''
        post_data = CommentSerializer(self.comment).data

        request = self.client.post(
            reverse(self.list_view_name, kwargs={'news_pk': self.news.id}),
            post_data,
            format='json'
        )

        self.assertEqual(
            request.data['content'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_comment_addition_with_too_long_content(self):
        self.client.force_authenticate(user=self.user)
        self.comment.content = 'Hey Jude!' * 1024
        post_data = CommentSerializer(self.comment).data

        request = self.client.post(
            reverse(self.list_view_name, kwargs={'news_pk': self.news.id}),
            post_data,
            format='json'
        )

        self.assertEqual(
            request.data['content'],
            ['Ensure this field has no more than 2048 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_comment_addition_with_valid_content(self):
        self.client.force_authenticate(user=self.user)
        self.comment.content = 'This is a very nice platorm, man!'
        post_data = CommentSerializer(self.comment).data

        request = self.client.post(
            reverse(self.list_view_name, kwargs={'news_pk': self.news.id}),
            post_data,
            format='json'
        )

        self.assertEqual(request.data['content'], self.comment.content)
        self.assertEqual(request.status_code, status.HTTP_201_CREATED)


    def test_comment_update_with_empty_content(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(
                self.detail_view_name,
                kwargs={'news_pk': self.news.id, 'pk': self.comment.id}
            ),
            {'content': ''},
            format='json'
        )

        self.assertEqual(
            request.data['content'], ['This field may not be blank.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_comment_update_of_another_user(self):
        self.client.force_authenticate(user=self.user)

        new_user = User.objects.create(username='test2', password='pass')
        new_student = Student.objects.create(user=new_user, clazz=self.clazz)
        self.comment.posted_by = new_student
        self.comment.save()

        request = self.client.put(
            reverse(
                self.detail_view_name,
                kwargs={'news_pk': self.news.id, 'pk': self.comment.id}
            ),
            {'content': 'I am stupid!!!'},
            format='json'
        )

        self.assertEqual(
            request.data['message'], 'You can edit only your own comments.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_comment_update_with_too_long_content(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(
                self.detail_view_name,
                kwargs={'news_pk': self.news.id, 'pk': self.comment.id}
            ),
            {'content': 'Hey Jude!' * 1024},
            format='json'
        )

        self.assertEqual(
            request.data['content'],
            ['Ensure this field has no more than 2048 characters.']
        )
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)


    def test_comment_update_with_valid_content(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.put(
            reverse(
                self.detail_view_name,
                kwargs={'news_pk': self.news.id, 'pk': self.comment.id}
            ),
            {'content': 'Hey Jude, don`t be afraid.'},
            format='json'
        )

        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_comment_deletion_with_invalid_news_id(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.delete(
            reverse(
                self.detail_view_name,
                kwargs={'news_pk': self.news.id + 1, 'pk': self.comment.id}
            )
        )

        self.assertEqual(request.data['detail'], 'Not found.')
        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)


    def test_comment_deletion_with_invalid_comment_id(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.delete(
            reverse(
                self.detail_view_name,
                kwargs={'news_pk': self.news.id, 'pk': self.comment.id + 1}
            )
        )

        self.assertEqual(request.data['detail'], 'Not found.')
        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)


    def test_comment_deletion_of_another_user(self):
        self.client.force_authenticate(user=self.user)

        new_user = User.objects.create(username='test3', password='pass')
        new_student = Student.objects.create(user=new_user, clazz=self.clazz)
        self.comment.posted_by = new_student
        self.comment.save()

        request = self.client.delete(
            reverse(
                self.detail_view_name,
                kwargs={'news_pk': self.news.id, 'pk': self.comment.id}
            )
        )

        self.assertEqual(
            request.data['message'], 'You can delete only your own comments.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_comment_deletion_with_valid_ids(self):
        self.client.force_authenticate(user=self.user)

        request = self.client.delete(
            reverse(
                self.detail_view_name,
                kwargs={'news_pk': self.news.id, 'pk': self.comment.id}
            )
        )

        self.assertEqual(
            request.data['message'], 'Comment successfully deleted.'
        )
        self.assertEqual(request.status_code, status.HTTP_200_OK)


class HomeworksViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_view_name = 'students:homeworks-list'
        self.detail_view_name = 'students:homeworks-detail'
        self.serializer_class = HomeworkSerializer

        self.subject = Subject.objects.create(title='test_subject')
        self.student_user = User.objects.create(username='test', password='pass')
        self.teacher_user = User.objects.create(username='author', password='pass123')
        self.group = Group.objects.create(name='Teachers')
        self.group.user_set.add(self.teacher_user)
        self.clazz = Class.objects.create(number=10, letter='A')
        self.student = Student.objects.create(user=self.student_user, clazz=self.clazz)
        self.homework = Homework.objects.create(
            subject=self.subject,
            clazz=self.clazz,
            deadline=datetime.now().date(),
            details='something interesting',
            author=self.teacher_user
        )


    def test_homeworks_with_anonymous_user(self):
        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(
            request.data['detail'],
            'Authentication credentials were not provided.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id})
        )

        self.assertEqual(
            request.data['detail'],
            'Authentication credentials were not provided.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_homeworks_with_authenticated_user(self):
        self.client.force_authenticate(user=self.student_user)

        request = self.client.get(reverse(self.list_view_name))

        self.assertIsNotNone(request.data)
        self.assertEqual(request.status_code, status.HTTP_200_OK)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id})
        )

        self.assertEqual(
            request.data['clazz']['number'], self.student.clazz.number
        )
        self.assertEqual(
            request.data['clazz']['letter'], self.student.clazz.letter
        )
        self.assertEqual(request.data['details'], self.homework.details)
        self.assertEqual(request.data['subject']['title'], self.subject.title)
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_homeworks_list_with_expired_date(self):
        self.client.force_authenticate(user=self.student_user)
        self.homework.deadline -= timedelta(days=5)
        self.homework.save()

        request = self.client.get(reverse(self.list_view_name))

        self.assertEqual(request.data, [])
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_homeworks_detail_with_invalid_id(self):
        self.client.force_authenticate(user=self.student_user)

        request = self.client.get(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id + 1})
        )

        self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)


    def test_homeworks_addition_with_student_account(self):
        self.client.force_authenticate(user=self.student_user)
        self.homework.details = 'С0002ГР'
        post_data = self.serializer_class(self.homework).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(
            request.data['detail'],
            'You do not have permission to perform this action.'
        )
        self.assertEqual(request.status_code, status.HTTP_403_FORBIDDEN)


    def test_homeworks_addition_with_too_long_details(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.homework.details = 'C0002ГР' * 256
        post_data = self.serializer_class(self.homework).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            request.data['details'],
            ['Ensure this field has no more than 256 characters.']
        )


    def test_homeworks_addition_with_valid_details(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.homework.details = 'C0002ГР'
        post_data = self.serializer_class(self.homework).data

        request = self.client.post(
            reverse(self.list_view_name), post_data, format='json'
        )

        self.assertEqual(request.status_code, status.HTTP_201_CREATED)


    def test_homeworks_update_with_student_account(self):
        self.client.force_authenticate(user=self.student_user)
        self.homework.details = 'С0002ГР'
        put_data = self.serializer_class(self.homework).data

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id}),
            put_data,
            format='json'
        )

        self.assertEqual(
            request.data['detail'],
            'You do not have permission to perform this action.'
        )
        self.assertEqual(request.status_code, status.HTTP_403_FORBIDDEN)


    def test_homeworks_update_with_too_long_details(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.homework.details = 'C0002ГР' * 256
        put_data = self.serializer_class(self.homework).data

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id}),
            put_data,
            format='json'
        )

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            request.data['details'],
            ['Ensure this field has no more than 256 characters.']
        )


    def test_homeworks_update_with_valid_details(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.homework.details = 'C0002ГР'
        put_data = self.serializer_class(self.homework).data

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id}),
            put_data,
            format='json'
        )

        self.assertEqual(request.data['details'], self.homework.details)
        self.assertEqual(request.status_code, status.HTTP_200_OK)


    def test_homeworks_update_of_another_user(self):
        self.client.force_authenticate(user=self.teacher_user)

        new_user = User.objects.create(username='test2', password='pass')
        self.group.user_set.add(new_user)
        self.homework.author = new_user
        self.homework.save()

        request = self.client.put(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id}),
            {'details': 'HAHAHA I AM ANONYMOUS!'},
            format='json'
        )

        self.assertEqual(
            request.data['message'], 'You can edit only your own homeworks.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_homeworks_deletion_of_another_user(self):
        self.client.force_authenticate(user=self.teacher_user)

        new_user = User.objects.create(username='test2', password='pass')
        self.group.user_set.add(new_user)
        self.homework.author = new_user
        self.homework.save()

        request = self.client.delete(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id})
        )

        self.assertEqual(
            request.data['message'], 'You can delete only your own homeworks.'
        )
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_homeworks_deletion(self):
        self.client.force_authenticate(user=self.teacher_user)

        request = self.client.delete(
            reverse(self.detail_view_name, kwargs={'pk': self.homework.id})
        )

        self.assertEqual(
            request.data['message'], 'Homework successfully deleted.'
        )
        self.assertEqual(request.status_code, status.HTTP_200_OK)
