import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import (
    SiteConfiguration, Service, PricingPlan, Project, BlogPost, 
    Testimonial, TeamMember, Lead, Order, CalendarEvent
)
from .payment_service import StripePaymentService
from .frappe_services import process_order_to_frappe
from .ai_agent_service import AIAgentService
from .calendar_service import GoogleCalendarService, book_appointment

logger = logging.getLogger(__name__)


def home(request):
    site_config = SiteConfiguration.objects.first()
    featured_services = Service.objects.filter(is_featured=True, is_active=True)[:3]
    featured_projects = Project.objects.filter(is_featured=True)[:6]
    featured_testimonials = Testimonial.objects.filter(is_featured=True, is_active=True)[:3]
    team_members = TeamMember.objects.filter(is_active=True)[:4]
    recent_blog_posts = BlogPost.objects.filter(status='published')[:3]
    
    context = {
        'site_config': site_config,
        'featured_services': featured_services,
        'featured_projects': featured_projects,
        'featured_testimonials': featured_testimonials,
        'team_members': team_members,
        'recent_blog_posts': recent_blog_posts,
    }
    
    return render(request, 'core/home.html', context)


def services(request):
    services_list = Service.objects.filter(is_active=True)
    pricing_plans = PricingPlan.objects.filter(is_active=True)
    
    context = {
        'services': services_list,
        'pricing_plans': pricing_plans,
    }
    
    return render(request, 'core/services.html', context)


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    related_services = Service.objects.filter(is_active=True).exclude(id=service.id)[:3]
    
    context = {
        'service': service,
        'related_services': related_services,
    }
    
    return render(request, 'core/service_detail.html', context)


def portfolio(request):
    projects_list = Project.objects.filter(status='completed')
    
    # Filter by technology if provided
    tech_filter = request.GET.get('tech')
    if tech_filter:
        projects_list = projects_list.filter(technologies__contains=[tech_filter])
    
    # Pagination
    paginator = Paginator(projects_list, 12)
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    # Get all unique technologies for filter
    all_technologies = set()
    for project in Project.objects.filter(status='completed'):
        all_technologies.update(project.technologies)
    
    context = {
        'projects': projects,
        'all_technologies': sorted(list(all_technologies)),
        'current_tech': tech_filter,
    }
    
    return render(request, 'core/portfolio.html', context)


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    related_projects = Project.objects.filter(status='completed').exclude(id=project.id)[:3]
    
    context = {
        'project': project,
        'related_projects': related_projects,
    }
    
    return render(request, 'core/project_detail.html', context)


def blog(request):
    blog_posts = BlogPost.objects.filter(status='published')
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        blog_posts = blog_posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__contains=[search_query])
        )
    
    # Pagination
    paginator = Paginator(blog_posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    # Get all unique tags
    all_tags = set()
    for post in BlogPost.objects.filter(status='published'):
        all_tags.update(post.tags)
    
    context = {
        'posts': posts,
        'all_tags': sorted(list(all_tags)),
        'search_query': search_query,
    }
    
    return render(request, 'core/blog.html', context)


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    related_posts = BlogPost.objects.filter(status='published').exclude(id=post.id)[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts,
    }
    
    return render(request, 'core/blog_detail.html', context)


def about(request):
    team_members = TeamMember.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True)[:6]
    
    context = {
        'team_members': team_members,
        'testimonials': testimonials,
    }
    
    return render(request, 'core/about.html', context)


def contact(request):
    if request.method == 'POST':
        try:
            lead_data = {
                'name': request.POST.get('name'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone', ''),
                'company': request.POST.get('company', ''),
                'message': request.POST.get('message', ''),
                'source': 'contact_form'
            }
            
            service_id = request.POST.get('service_interest')
            if service_id:
                try:
                    service = Service.objects.get(id=service_id)
                    lead_data['service_interest'] = service
                except Service.DoesNotExist:
                    pass
            
            lead = Lead.objects.create(**lead_data)
            
            # Notify AI agent about new lead
            try:
                ai_agent = AIAgentService()
                ai_agent.notify_new_lead(lead)
            except Exception as e:
                logger.error(f"Failed to notify AI agent about new lead: {e}")
            
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
            
        except Exception as e:
            logger.error(f"Error processing contact form: {e}")
            messages.error(request, 'There was an error sending your message. Please try again.')
    
    services_list = Service.objects.filter(is_active=True)
    
    context = {
        'services': services_list,
    }
    
    return render(request, 'core/contact.html', context)


def pricing(request):
    pricing_plans = PricingPlan.objects.filter(is_active=True)
    services_list = Service.objects.filter(is_active=True)
    
    context = {
        'pricing_plans': pricing_plans,
        'services': services_list,
    }
    
    return render(request, 'core/pricing.html', context)


@require_http_methods(["POST"])
def checkout(request):
    try:
        service_id = request.POST.get('service_id')
        pricing_plan_id = request.POST.get('pricing_plan_id')
        customer_name = request.POST.get('customer_name')
        customer_email = request.POST.get('customer_email')
        customer_phone = request.POST.get('customer_phone', '')
        
        if not customer_name or not customer_email:
            return JsonResponse({'error': 'Name and email are required'}, status=400)
        
        # Create order
        order_data = {
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone
        }
        
        if service_id:
            service = Service.objects.get(id=service_id)
            order_data.update({
                'service': service,
                'amount': service.price or 0
            })
        elif pricing_plan_id:
            pricing_plan = PricingPlan.objects.get(id=pricing_plan_id)
            order_data.update({
                'pricing_plan': pricing_plan,
                'amount': pricing_plan.price
            })
        else:
            return JsonResponse({'error': 'Service or pricing plan required'}, status=400)
        
        order = Order.objects.create(**order_data)
        
        # Create Stripe checkout session
        stripe_service = StripePaymentService()
        session_data = {
            'order_id': order.order_id,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'service_id': service_id,
            'pricing_plan_id': pricing_plan_id
        }
        
        session = stripe_service.create_checkout_session(session_data, request)
        
        order.stripe_session_id = session.id
        order.save()
        
        return JsonResponse({
            'checkout_url': session.url,
            'session_id': session.id
        })
        
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        return JsonResponse({'error': 'Failed to create checkout session'}, status=500)


def payment_success(request):
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid payment session')
        return redirect('home')
    
    try:
        stripe_service = StripePaymentService()
        session = stripe_service.retrieve_session(session_id)
        order = stripe_service.handle_successful_payment(session)
        
        if order:
            # Process order to Frappe
            try:
                process_order_to_frappe(order.order_id)
            except Exception as e:
                logger.error(f"Failed to process order to Frappe: {e}")
            
            # Notify AI agent
            try:
                ai_agent = AIAgentService()
                ai_agent.notify_payment_success(order)
            except Exception as e:
                logger.error(f"Failed to notify AI agent about payment: {e}")
            
            context = {
                'order': order,
                'session': session
            }
            return render(request, 'core/payment_success.html', context)
        else:
            messages.error(request, 'Payment processed but order not found')
            return redirect('home')
            
    except Exception as e:
        logger.error(f"Payment success error: {e}")
        messages.error(request, 'Error processing payment confirmation')
        return redirect('home')


def payment_cancelled(request):
    messages.info(request, 'Payment was cancelled')
    return render(request, 'core/payment_cancelled.html')


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    stripe_service = StripePaymentService()
    success = stripe_service.handle_webhook(payload, sig_header)
    
    if success:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


@csrf_exempt
@require_http_methods(["POST"])
def ai_agent_webhook(request):
    try:
        data = json.loads(request.body)
        webhook_type = data.get('type')
        
        ai_agent = AIAgentService()
        result = ai_agent.process_webhook_data(webhook_type, data)
        
        return JsonResponse({'status': 'success', 'result': result})
        
    except Exception as e:
        logger.error(f"AI agent webhook error: {e}")
        return JsonResponse({'error': 'Webhook processing failed'}, status=500)


@require_http_methods(["GET"])
def api_services(request):
    services_list = Service.objects.filter(is_active=True).values(
        'id', 'title', 'description', 'price', 'price_type', 'features'
    )
    return JsonResponse({'services': list(services_list)})


@require_http_methods(["GET"])
def api_pricing(request):
    pricing_plans = PricingPlan.objects.filter(is_active=True).values(
        'id', 'name', 'description', 'price', 'price_period', 'features'
    )
    return JsonResponse({'pricing_plans': list(pricing_plans)})


@require_http_methods(["POST"])
def api_lead(request):
    try:
        data = json.loads(request.body)
        
        lead_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone', ''),
            'company': data.get('company', ''),
            'message': data.get('message', ''),
            'source': data.get('source', 'api')
        }
        
        service_id = data.get('service_id')
        if service_id:
            try:
                service = Service.objects.get(id=service_id)
                lead_data['service_interest'] = service
            except Service.DoesNotExist:
                pass
        
        lead = Lead.objects.create(**lead_data)
        
        return JsonResponse({
            'status': 'success',
            'lead_id': lead.id,
            'message': 'Lead created successfully'
        })
        
    except Exception as e:
        logger.error(f"API lead creation error: {e}")
        return JsonResponse({'error': 'Failed to create lead'}, status=500)


def calendar_auth(request):
    calendar_service = GoogleCalendarService()
    auth_url, state = calendar_service.get_authorization_url()
    
    request.session['calendar_state'] = state
    return redirect(auth_url)


def calendar_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    session_state = request.session.get('calendar_state')
    
    if not code or state != session_state:
        messages.error(request, 'Invalid calendar authorization')
        return redirect('contact')
    
    try:
        calendar_service = GoogleCalendarService()
        credentials = calendar_service.exchange_code_for_tokens(code, state)
        
        request.session['calendar_credentials'] = credentials
        messages.success(request, 'Calendar authorized successfully!')
        
        return redirect('book_appointment')
        
    except Exception as e:
        logger.error(f"Calendar callback error: {e}")
        messages.error(request, 'Failed to authorize calendar access')
        return redirect('contact')


def book_appointment_view(request):
    if request.method == 'POST':
        try:
            credentials = request.session.get('calendar_credentials')
            if not credentials:
                return redirect('calendar_auth')
            
            appointment_data = {
                'name': request.POST.get('name'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone', ''),
                'service': request.POST.get('service', ''),
                'message': request.POST.get('message', ''),
                'start_time': datetime.fromisoformat(request.POST.get('start_time')),
                'end_time': datetime.fromisoformat(request.POST.get('end_time'))
            }
            
            calendar_event = book_appointment(appointment_data, credentials)
            
            messages.success(request, f'Appointment booked successfully! Event ID: {calendar_event.google_event_id}')
            return redirect('contact')
            
        except Exception as e:
            logger.error(f"Appointment booking error: {e}")
            messages.error(request, 'Failed to book appointment')
    
    services_list = Service.objects.filter(is_active=True)
    
    context = {
        'services': services_list,
    }
    
    return render(request, 'core/book_appointment.html', context)


@require_http_methods(["GET"])
def health_check(request):
    try:
        # Check database connection
        SiteConfiguration.objects.exists()
        
        # Check external services
        health_status = {
            'database': 'healthy',
            'frappe': 'unknown',
            'ai_agent': 'unknown',
            'timestamp': timezone.now().isoformat()
        }
        
        # Check Frappe connection
        try:
            from .frappe_services import FrappeService
            frappe_service = FrappeService()
            if frappe_service.health_check():
                health_status['frappe'] = 'healthy'
            else:
                health_status['frappe'] = 'unhealthy'
        except Exception:
            health_status['frappe'] = 'error'
        
        # Check AI Agent connection
        try:
            ai_agent = AIAgentService()
            if ai_agent.health_check():
                health_status['ai_agent'] = 'healthy'
            else:
                health_status['ai_agent'] = 'unhealthy'
        except Exception:
            health_status['ai_agent'] = 'error'
        
        return JsonResponse(health_status)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JsonResponse({
            'database': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)