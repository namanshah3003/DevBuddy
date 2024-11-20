from django.contrib import admin
from .models import User, Team,Hackathon,Organization
# Post, Team, TeamMember, Hackathon, Project, Issue, Comment

# Register your models here.
admin.site.register(User)
admin.site.register(Hackathon)
admin.site.register(Organization)
admin.site.register(Team)
# admin.site.register(Issue)
# admin.site.register(Comment)
admin.site.site_header = "Hackathon Management Hub"
admin.site.site_title = "Hackathon Management Hub Portal"
admin.site.index_title = "Welcome to Hackathon Management Hub Portal"