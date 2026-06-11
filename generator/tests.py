from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import GeneratedContent, APIKeySetting

class AIContentGeneratorTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "testuser"
        self.email = "testuser@example.com"
        self.password = "SecurePassword123!"
        
        # Create user for authentication tests
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )
        # Setup API Keys profile
        self.api_keys = APIKeySetting.objects.create(user=self.user)

    def test_user_registration(self):
        # Register a new user
        reg_username = "newuser"
        response = self.client.post(reverse('register'), {
            'username': reg_username,
            'email': "newuser@example.com",
            'password': "NewSecurePassword456!",
            'password_confirm': "NewSecurePassword456!"
        })
        # Verify redirect to dashboard on success
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username=reg_username).exists())
        
        # Verify default api key profile is created
        new_user = User.objects.get(username=reg_username)
        self.assertTrue(APIKeySetting.objects.filter(user=new_user).exists())

    def test_user_login(self):
        # Authenticate with credentials
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, 302) # redirect to dashboard
        
        # Logout to test wrong credentials
        self.client.logout()
        
        # Test with wrong credentials
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': "WrongPassword"
        })
        self.assertEqual(response.status_code, 200) # stays on page with error

    def test_dashboard_login_required(self):
        # Accessing dashboard without logging in should redirect
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

        # Access dashboard after logging in
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'generator/dashboard.html')

    def test_save_api_keys(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('save_api_keys'), {
            'openai_api_key': 'test-openai-key',
            'groq_api_key': 'test-groq-key'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check DB updates
        self.api_keys.refresh_from_db()
        self.assertEqual(self.api_keys.openai_api_key, 'test-openai-key')
        self.assertEqual(self.api_keys.groq_api_key, 'test-groq-key')

    def test_generate_blog_mock_fallback(self):
        self.client.login(username=self.username, password=self.password)
        
        # Send generation request
        response = self.client.post(reverse('generate_blog'), {
            'topic': 'Benefits of AI',
            'tone': 'Casual',
            'style': 'SEO-friendly'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['content_type'], 'blog')
        self.assertIn('Topic: Benefits of AI', data['prompt'])
        self.assertIn('# The Master Guide to:', data['generated_text']) # Verify mock generator text format
        
        # Verify content was saved to DB
        self.assertTrue(GeneratedContent.objects.filter(user=self.user, content_type='blog').exists())

    def test_history_endpoints(self):
        self.client.login(username=self.username, password=self.password)
        
        # Create a mock content item in DB
        content = GeneratedContent.objects.create(
            user=self.user,
            content_type='product',
            prompt='Product: Earbuds',
            generated_text='Fabulous wireless earbuds copy'
        )
        
        # Test list endpoint
        response = self.client.get(reverse('history_list'))
        self.assertEqual(response.status_code, 200)
        list_data = response.json()
        self.assertTrue(list_data['success'])
        self.assertEqual(len(list_data['history']), 1)
        self.assertEqual(list_data['history'][0]['id'], content.id)

        # Test detail endpoint
        response = self.client.get(reverse('history_detail', args=[content.id]))
        self.assertEqual(response.status_code, 200)
        detail_data = response.json()
        self.assertTrue(detail_data['success'])
        self.assertEqual(detail_data['generated_text'], 'Fabulous wireless earbuds copy')

        # Test searching history
        response = self.client.get(reverse('history_list') + '?search=Earbuds')
        self.assertEqual(response.status_code, 200)
        search_data = response.json()
        self.assertEqual(len(search_data['history']), 1)

        response = self.client.get(reverse('history_list') + '?search=NonExistent')
        self.assertEqual(response.status_code, 200)
        search_data_empty = response.json()
        self.assertEqual(len(search_data_empty['history']), 0)
