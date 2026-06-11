import json
import os
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils.decorators import method_decorator

from django.db.models import Q
from .models import GeneratedContent, APIKeySetting

# Helpers for AI Integration
def get_user_api_keys(user):
    """Retrieve keys from settings or environment variables."""
    openai_key = ""
    groq_key = ""
    
    # Try fetching from DB
    try:
        setting = APIKeySetting.objects.get(user=user)
        openai_key = setting.openai_api_key
        groq_key = setting.groq_api_key
    except APIKeySetting.DoesNotExist:
        pass
        
    # Fallback to environment variables if not set in DB
    if not openai_key:
        openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not groq_key:
        groq_key = os.environ.get("GROQ_API_KEY", "")
        
    return openai_key, groq_key


def run_openai_generation(api_key, system_prompt, user_prompt):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message.content


def run_groq_generation(api_key, system_prompt, user_prompt):
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message.content


def generate_mock_content(content_type, user_prompt_dict):
    """Generates extremely rich and detailed mock content when no API keys are provided."""
    import time
    time.sleep(1.2) # Simulate network lag for realistic visual effect
    
    if content_type == 'blog':
        topic = user_prompt_dict.get('topic', 'Digital Marketing')
        tone = user_prompt_dict.get('tone', 'Informative')
        style = user_prompt_dict.get('style', 'SEO-friendly')
        
        return f"""# The Master Guide to: {topic.title()}

*Published on: {datetime.now().strftime('%B %d, %Y')} | Tone: {tone} | Style: {style}*

---

Artificial Intelligence and digital transformation are reshaping our world. When discussing **{topic}**, the significance cannot be overstated. In this guide, we dive deep into key strategies, actionable insights, and the core elements you need to succeed.

## Introduction: Why {topic} Matters Today
In the modern landscape, staying ahead of trends requires a solid foundation. Whether you are a business owner, developer, or creator, understanding the nuances of {topic} is key. The landscape changes rapidly, and adapting is the difference between thriving and falling behind.

## Key Strategies for Success
To maximize your impact, focus on these three core pillars:

1. **Strategic Integration:** Always align your goals with standard data insights.
2. **Quality-First Approach:** Ensure your audience gets value, not fluff.
3. **Continuous Iteration:** Run experiments, gather feedback, and adapt.

### Optimizing for Best Results
When applying these techniques, consistency is your superpower. Plan your milestones and stay the course.

---

## Actionable Takeaways
- **Start Small:** Implement one new idea today.
- **Track Metrics:** Never guess what is working.
- **Learn Constantly:** The best practitioners are lifelong students.

*This SEO-optimized guide is ready to share!*"""

    elif content_type == 'product':
        product_name = user_prompt_dict.get('product_name', 'Wireless Earbuds')
        features = user_prompt_dict.get('features', 'Noise-canceling, 24h battery life')
        
        return f"""# Premium Product Listing: {product_name.title()}

## Discover Unmatched Performance

Elevate your daily routine with the all-new **{product_name}**. Engineered for demanding lifestyles, this product blends premium design with state-of-the-art functionality.

### Key Features & Benefits:
- **Outstanding Capability:** Built specifically to address: *{features}*.
- **Ergonomic Craftsmanship:** Sleek, lightweight construction ensures comfortable long-term usage.
- **Intuitive Integration:** Easy setup that fits seamlessly into your existing ecosystem.

### What's In The Box:
1. {product_name} Core Device
2. Type-C Fast Charging Cable
3. Premium Hard Carrying Case
4. User Instruction Manual & 1-Year Warranty Card

---
*Transform the way you work, play, and live. Experience {product_name} today.*"""

    elif content_type == 'caption':
        topic = user_prompt_dict.get('topic', 'Product Launch')
        platform = user_prompt_dict.get('platform', 'Instagram')
        tone = user_prompt_dict.get('tone', 'Creative')
        
        hashtags = "#" + " #".join([w.lower().replace(" ", "") for w in topic.split(",")[:4]])
        if not hashtags.strip() or hashtags == "#":
            hashtags = "#innovation #ai #contentgenerator #productivity"

        return f"""📱 Optimized Caption for: **{platform}** (Tone: {tone})

✨ Say hello to the future! ✨

We are thrilled to present our latest: **{topic}**! 🚀

Whether you want to streamline your workflow, boost your team's creativity, or just save hours of manual writing every single day, this is designed for YOU. We've spent months refining every detail to make sure it delivers value from day one.

Let us know what you think in the comments below! 👇

👉 Tap the link in our bio to learn more and get started.

---
{hashtags} #launch #trending #solutions"""

    return "No mock content generated."


def generate_content_core(user, content_type, prompt_data):
    """Core function to route AI queries or fall back to mock generation."""
    openai_key, groq_key = get_user_api_keys(user)
    
    # Structure system and user prompts
    if content_type == 'blog':
        system_prompt = "You are a professional blog post writer and SEO expert. Generate a detailed, engaging blog article in clean markdown format based on the topic. Use clear headings."
        user_prompt = f"Topic: {prompt_data.get('topic')}\nTone: {prompt_data.get('tone')}\nStyle: {prompt_data.get('style')}"
    elif content_type == 'product':
        system_prompt = "You are a conversion-focused e-commerce copywriter. Generate an engaging, professional product description in markdown highlighting key features and benefits."
        user_prompt = f"Product Name: {prompt_data.get('product_name')}\nKey Features: {prompt_data.get('features')}"
    else: # caption
        system_prompt = "You are a social media manager. Generate a high-performing social media caption optimized for the specified platform. Include relevant emojis and automatically append 5-7 popular hashtags."
        user_prompt = f"Topic/Campaign: {prompt_data.get('topic')}\nPlatform: {prompt_data.get('platform')}\nTone: {prompt_data.get('tone')}"

    # Route request
    try:
        if openai_key:
            generated_text = run_openai_generation(openai_key, system_prompt, user_prompt)
        elif groq_key:
            generated_text = run_groq_generation(groq_key, system_prompt, user_prompt)
        else:
            generated_text = generate_mock_content(content_type, prompt_data)
    except Exception as e:
        # Fallback to mock if API calls error out (e.g. invalid key/rate limit)
        generated_text = f"**[AI Request failed: {str(e)}. Falling back to Preview/Mock Mode]**\n\n" + generate_mock_content(content_type, prompt_data)
        
    return generated_text


# Authentication Views
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        if not username or not email or not password:
            messages.error(request, "Please fill in all fields.")
            return render(request, 'generator/register.html')
            
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'generator/register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'generator/register.html')
            
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            # Create default API key entry
            APIKeySetting.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'generator/register.html')
            
    return render(request, 'generator/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'generator/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


# Main Application Dashboard
@login_required
def dashboard_view(request):
    # Ensure settings object exists
    settings_obj, created = APIKeySetting.objects.get_or_create(user=request.user)
    
    # Get initial history items
    history_items = GeneratedContent.objects.filter(user=request.user)
    
    context = {
        'history_items': history_items,
        'openai_key': settings_obj.openai_api_key,
        'groq_key': settings_obj.groq_api_key,
    }
    return render(request, 'generator/dashboard.html', context)


# Generation Endpoints (AJAX POST)
@login_required
def generate_blog(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
        
    topic = request.POST.get('topic', '').strip()
    tone = request.POST.get('tone', 'Informative')
    style = request.POST.get('style', 'SEO-friendly')
    
    if not topic:
        return JsonResponse({'success': False, 'error': 'Topic is required'}, status=400)
        
    prompt_data = {'topic': topic, 'tone': tone, 'style': style}
    generated_text = generate_content_core(request.user, 'blog', prompt_data)
    
    # Save to Database
    content = GeneratedContent.objects.create(
        user=request.user,
        content_type='blog',
        prompt=f"Topic: {topic} | Tone: {tone} | Style: {style}",
        generated_text=generated_text
    )
    
    return JsonResponse({
        'success': True,
        'id': content.id,
        'content_type': 'blog',
        'prompt': content.prompt,
        'generated_text': content.generated_text,
        'created_at': content.created_at.strftime('%Y-%m-%d %H:%M')
    })


@login_required
def generate_product(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
        
    product_name = request.POST.get('product_name', '').strip()
    features = request.POST.get('features', '').strip()
    
    if not product_name:
        return JsonResponse({'success': False, 'error': 'Product name is required'}, status=400)
        
    prompt_data = {'product_name': product_name, 'features': features}
    generated_text = generate_content_core(request.user, 'product', prompt_data)
    
    # Save to Database
    content = GeneratedContent.objects.create(
        user=request.user,
        content_type='product',
        prompt=f"Product: {product_name} | Features: {features[:50]}...",
        generated_text=generated_text
    )
    
    return JsonResponse({
        'success': True,
        'id': content.id,
        'content_type': 'product',
        'prompt': content.prompt,
        'generated_text': content.generated_text,
        'created_at': content.created_at.strftime('%Y-%m-%d %H:%M')
    })


@login_required
def generate_caption(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
        
    topic = request.POST.get('topic', '').strip()
    platform = request.POST.get('platform', 'Instagram')
    tone = request.POST.get('tone', 'Creative')
    
    if not topic:
        return JsonResponse({'success': False, 'error': 'Topic/Campaign is required'}, status=400)
        
    prompt_data = {'topic': topic, 'platform': platform, 'tone': tone}
    generated_text = generate_content_core(request.user, 'caption', prompt_data)
    
    # Save to Database
    content = GeneratedContent.objects.create(
        user=request.user,
        content_type='caption',
        prompt=f"Topic: {topic} | Platform: {platform} | Tone: {tone}",
        generated_text=generated_text
    )
    
    return JsonResponse({
        'success': True,
        'id': content.id,
        'content_type': 'caption',
        'prompt': content.prompt,
        'generated_text': content.generated_text,
        'created_at': content.created_at.strftime('%Y-%m-%d %H:%M')
    })


# Settings Endpoints (AJAX POST)
@login_required
def save_api_keys(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
        
    openai_key = request.POST.get('openai_api_key', '').strip()
    groq_key = request.POST.get('groq_api_key', '').strip()
    
    settings_obj, created = APIKeySetting.objects.get_or_create(user=request.user)
    settings_obj.openai_api_key = openai_key
    settings_obj.groq_api_key = groq_key
    settings_obj.save()
    
    return JsonResponse({'success': True, 'message': 'API keys updated successfully!'})


# History Endpoints
@login_required
def history_list(request):
    search_query = request.GET.get('search', '').strip()
    
    items = GeneratedContent.objects.filter(user=request.user)
    if search_query:
        items = items.filter(
            Q(prompt__icontains=search_query) | 
            Q(generated_text__icontains=search_query)
        )
        
    data = []
    for c in items:
        data.append({
            'id': c.id,
            'content_type': c.content_type,
            'prompt': c.prompt,
            'generated_text': c.generated_text,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M')
        })
        
    return JsonResponse({'success': True, 'history': data})


@login_required
def history_detail(request, item_id):
    try:
        content = GeneratedContent.objects.get(id=item_id, user=request.user)
        return JsonResponse({
            'success': True,
            'id': content.id,
            'content_type': content.content_type,
            'prompt': content.prompt,
            'generated_text': content.generated_text,
            'created_at': content.created_at.strftime('%b %d, %Y %I:%M %p')
        })
    except GeneratedContent.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Content item not found'}, status=404)
