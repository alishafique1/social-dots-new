from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteConfiguration, TeamMember, Service, PricingPlan, Project, 
    BlogPost, Testimonial, Lead, Order, CalendarEvent, AIAgentLog
)


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'email', 'contact_email', 'phone', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'tagline', 'logo', 'logo_dark', 'favicon', 'website_url')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'contact_email', 'address')
        }),
        ('Brand Colors', {
            'fields': ('primary_color', 'secondary_color', 'accent_color'),
            'description': 'Social Dots brand colors based on company guidelines'
        }),
        ('Social Media', {
            'fields': ('social_facebook', 'social_twitter', 'social_linkedin', 'social_instagram')
        }),
        ('SEO & Analytics', {
            'fields': ('meta_description', 'google_analytics_id')
        }),
        ('Business Information', {
            'fields': ('legal_name', 'business_number'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'email', 'is_active', 'order']
    list_filter = ['is_active', 'position']
    search_fields = ['name', 'position', 'email']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'price_type', 'is_featured', 'is_active', 'order']
    list_filter = ['price_type', 'is_featured', 'is_active']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_featured', 'is_active']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order', 'title']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'icon', 'image')
        }),
        ('Pricing', {
            'fields': ('price', 'price_type', 'stripe_price_id')
        }),
        ('Features & Settings', {
            'fields': ('features', 'is_featured', 'is_active', 'order')
        }),
    )


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'price_period', 'is_popular', 'is_active', 'order']
    list_filter = ['price_period', 'is_popular', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['order', 'is_popular', 'is_active']
    ordering = ['order', 'price']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'client_name', 'status', 'is_featured', 'start_date', 'end_date']
    list_filter = ['status', 'is_featured', 'start_date']
    search_fields = ['title', 'client_name', 'description']
    list_editable = ['status', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'client_name', 'description', 'image')
        }),
        ('Project Details', {
            'fields': ('technologies', 'project_url', 'github_url', 'gallery')
        }),
        ('Timeline & Status', {
            'fields': ('status', 'start_date', 'end_date')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'order')
        }),
    )


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'is_featured', 'published_at', 'created_at']
    list_filter = ['status', 'is_featured', 'author', 'published_at']
    search_fields = ['title', 'content', 'tags']
    list_editable = ['status', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'excerpt', 'content', 'featured_image')
        }),
        ('Publication', {
            'fields': ('status', 'published_at', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_description', 'tags')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'client_company', 'rating', 'is_featured', 'is_active', 'order']
    list_filter = ['rating', 'is_featured', 'is_active']
    search_fields = ['client_name', 'client_company', 'content']
    list_editable = ['rating', 'is_featured', 'is_active', 'order']
    ordering = ['order', '-created_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'company', 'service_interest', 'status', 'created_at']
    list_filter = ['status', 'service_interest', 'source', 'created_at']
    search_fields = ['name', 'email', 'company', 'message']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('Inquiry Details', {
            'fields': ('service_interest', 'message', 'budget', 'timeline')
        }),
        ('Lead Management', {
            'fields': ('status', 'source', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer_name', 'customer_email', 'amount', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['order_id', 'customer_name', 'customer_email', 'stripe_payment_intent_id']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'service', 'pricing_plan', 'amount', 'currency', 'status')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Payment Details', {
            'fields': ('stripe_payment_intent_id', 'stripe_session_id')
        }),
        ('Integration', {
            'fields': ('frappe_document_id', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'attendee_name', 'start_time', 'end_time', 'is_confirmed']
    list_filter = ['is_confirmed', 'start_time']
    search_fields = ['title', 'attendee_name', 'attendee_email']
    list_editable = ['is_confirmed']
    date_hierarchy = 'start_time'
    ordering = ['start_time']

    fieldsets = (
        ('Event Details', {
            'fields': ('title', 'description', 'start_time', 'end_time')
        }),
        ('Attendee Information', {
            'fields': ('attendee_name', 'attendee_email', 'attendee_phone')
        }),
        ('Integration', {
            'fields': ('google_event_id', 'is_confirmed')
        }),
    )


@admin.register(AIAgentLog)
class AIAgentLogAdmin(admin.ModelAdmin):
    list_display = ['log_type', 'user_identifier', 'status', 'created_at']
    list_filter = ['log_type', 'status', 'created_at']
    search_fields = ['user_identifier', 'message_content', 'response_content']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Log Information', {
            'fields': ('log_type', 'user_identifier', 'status')
        }),
        ('Content', {
            'fields': ('message_content', 'response_content')
        }),
        ('Webhook Data', {
            'fields': ('webhook_data',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.site_header = "Social Dots Inc. Administration"
admin.site.site_title = "Social Dots Admin"
admin.site.index_title = "Welcome to Social Dots Administration"