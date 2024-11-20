from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
import requests
from .models import Team, User, Project, Hackathon, Tags,Organization,Chat
from .predictor import recommend_users
from django.db.models import Q
from django.contrib import messages  # Import messages for displaying feedback

# Create your views here.

@login_required(login_url='/login/')
def home(request):
    git_user=request.user.username
    print(git_user)
    url = f"https://api.github.com/users/{git_user}"
    r = requests.get(url.format(git_user)).json()
    #print(r)
    #save in models
    Name = r['name']
    Bio = r['bio']
    Location = r['location']
    Company = r['company']
    Email = r['email']
    Public_repos = r['public_repos']
    Followers = r['followers']
    Following = r['following']
    avatar_url = r['avatar_url']
    #save in User model
    request.user.name = Name
    request.user.bio = Bio
    request.user.location = Location
    request.user.company = Company
    request.user.email = Email
    request.user.public_repos = Public_repos
    request.user.followers = Followers
    request.user.following = Following
    request.user.avatar = avatar_url
    request.user.save()
    return redirect('profile')

@login_required(login_url='/login/')
def profile(request):
    user_profile = User.objects.get(username=request.user.username)
    user_tags = Tags.objects.filter(coder=user_profile)
    invited_teams = user_profile.invites.all()
    user_teams = user_profile.teams.all()
    team_ids=[]
    team_names=[]
    for team in invited_teams:
        team_ids.append(team.id)
        team_names.append(team.name)
    if request.method=='POST':
        name = request.POST['teamname']
        description = request.POST['teamdesc']
        print(name, description)
        team=Team(name=name, description=description, teamleader=request.user)
        team.save()
        team.accepted_members.add(request.user)
        team.save()
        request.user.teams.add(team)
        request.user.save()
        message = "Created team successfully!" 
    return render(request, 'base/profile.html', {'user_profile':user_profile, 'team_id':team_ids, 'team_names':team_names, 'user_teams':user_teams, 'user_tags':user_tags,'team_count':len(user_teams)})
@login_required(login_url='/login/')
def addmember(request,id):
    if request.method == 'POST':
        membername = request.POST['username']
        print(membername)
        print(id)
        mem = User.objects.get(username=membername)
        if mem:
            team = Team.objects.get(id=id)
            team.invited_members.add(mem)
            mem.invites.add(team)
            team.save()
            mem.save()
    else:
        #return message that user not found
        message = "User not found"
        #return render(request, 'base/home.html', {'message':message})
    return redirect('home')

@login_required(login_url='/login/')
def createteam(request):
    if request.method == 'POST':
        name = request.POST['teamname']
        description = request.POST['teamdesc']
        print(name, description)
        if Team.objects.filter(name=name).exists():
            message = "Team name already exists!"
            return render(request, 'base/createteam.html', {'message':message})
        team=Team(name=name, description=description, teamleader=request.user)
        team.save()
        team.accepted_members.add(request.user)
        team.save()
        request.user.teams.add(team)
        request.user.save()
        message = "Created team successfully!"
        return render(request, 'base/home.html', {'message':message,})
    return render(request, 'base/createteam.html')

@login_required(login_url='/login/')
def delete_team(request, id):
    team = get_object_or_404(Team, id=id)
    if request.user == team.teamleader:
        # Remove the team from all associated hackathons
        hackathons = Hackathon.objects.filter(teams=team)
        for hackathon in hackathons:
            hackathon.teams.remove(team)
        
        # Delete all projects associated with the team
        projects = Project.objects.filter(pteam=team)
        for project in projects:
            project.delete()
        
        # Remove the team from all users' teams field
        users = User.objects.filter(teams=team)
        for user in users:
            user.teams.remove(team)
            user.save()
        
        # Delete the team
        team.delete()
        messages.success(request, "Team deleted successfully!")
        return redirect('teams')
    else:
        messages.error(request, "You are not authorized to delete this team.")
        return redirect('teams')
    

@login_required(login_url='/login/')
def teams(request):
    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        project_url = request.POST.get('project_url')
        team = get_object_or_404(Team, id=team_id)
        
        if project_url:
            project, created = Project.objects.get_or_create(pteam=team)
            project.repo_url = project_url
            project.save()
            messages.success(request, "Project URL added successfully!")
        else:
            messages.error(request, "Project URL cannot be empty.")
        return redirect('teams')

    team_list = request.user.teams.all()
    combined_list = []
    for team in team_list:
        hackathons = Hackathon.objects.filter(teams=team)
        project = Project.objects.filter(pteam=team).first()
        combined_list.append((team, hackathons, project))

    return render(request, 'base/displayteams.html', {'combined_list': combined_list})

@login_required(login_url='/login/')
def team(request, id):
    team = get_object_or_404(Team, id=id)
    accepted_members = team.accepted_members.all()
    invited_members = team.invited_members.all()
    
    # Prepare member lists for rendering
    id_list = []
    mem_list = []
    for member in accepted_members:
        mem_list.append(member.username)
    id_list.append(mem_list)
    
    if request.method == 'POST':
        membername = request.POST.get('username')
        try:
            mem = User.objects.get(username=membername)
            
            if mem in accepted_members:
                messages.error(request, f"{membername} is already an accepted member of the team.")
            elif mem in invited_members:
                messages.error(request, f"{membername} is already invited to the team.")
            else:
                # Add member to the invited list
                team.invited_members.add(mem)
                mem.invites.add(team)
                team.save()
                mem.save()
                messages.success(request, f"Invitation sent to {membername} successfully!")
        except User.DoesNotExist:
            messages.error(request, f"User '{membername}' does not exist.")
    
    return render(request, 'base/teamdetails.html', {'team': team, 'id_list': id_list})

@login_required(login_url='/login/')
def projects(request,id):
    if request.method == 'POST':
        pname=request.POST['projectname']
        url=request.POST['projecturl']
        team = Team.objects.get(id=id)
        p=Project(name=pname, url=url, team=team)
        p.save()
        return render(request, 'base/projects.html', {'team':team})
    return render(request, 'base/projects.html')

@login_required(login_url='/login/')
def acceptinvite(request, teamname):
    team = Team.objects.get(name=teamname)
    team.accepted_members.add(request.user)
    team.invited_members.remove(request.user)
    request.user.teams.add(team)
    request.user.invites.remove(team)
    team.save()
    request.user.save()
    return redirect('profile')

@login_required(login_url='/login/')
def rejectinvite(request, teamname):
    team = Team.objects.get(name=teamname)
    team.invited_members.remove(request.user)
    team.save()
    request.user.invites.remove(team)
    request.user.save()
    return redirect('profile')

# @login_required(login_url='/loginOrg/')
def create_hackathon(request,name):
    organization = Organization.objects.get(name=name)
    hackathons = list(organization.hackathons.all())
    no_of_hackathons = Organization.objects.get(name=name).hackathons.count()
    print(no_of_hackathons)
    if request.method == 'POST':
        name = request.POST['hackathonname']
        description = request.POST['hackathondesc']
        print(name, description)
        hackathon=Hackathon(name=name, description=description)
        hackathon.save()
        organization.hackathons.add(hackathon)
        organization.save()
        message = "Created hackathon successfully!"
        hackathons = list(organization.hackathons.all())
        no_of_hackathons +=1
        return render(request, 'base/orgyhackathon.html', {'organization':organization, 'no_of_hackathons':no_of_hackathons, 'message':message, 'hackathons':hackathons})
    print(hackathons)
    return render(request, 'base/orgyhackathon.html', {'organization':organization, 'no_of_hackathons':no_of_hackathons, 'hackathons':hackathons})

@login_required(login_url='/login/')
def register_hackathon(request, hack):
    user = request.user
    if request.method == 'POST':
        hackathon = Hackathon.objects.get(name=hack)
        team_name = request.POST['teamname']
        try:
            team = Team.objects.get(name=team_name)
            hackathon.teams.add(team)
            hackathon.save()
            return redirect('profile')
        except Team.DoesNotExist:
            messages.error(request, f"Team '{team_name}' does not exist.")
            return redirect('uhackathon', hack=hack)

    #generate a random dictionary consistings of teams
    h = Hackathon.objects.get(name=hack)
    o = Organization.objects.all()
    org = None
    for i in o:
        if h in i.hackathons.all():
            org = i
    #get organization of the hackathon
    # list_hack=list(h)
    # o = org[0]
    t = h.teams.all().count()
    te =list( h.teams.all())
    tea = list(user.teams.all())
    return render(request, 'base/uhackathon.html', {'tea':tea, 'h':h,'t':t, 'org':org,'te':te})

@login_required(login_url='/login/')
def tags(request):
    if request.method == 'POST':
        tagname = request.POST['tagname']
        u=request.POST['username']
        coder=User.objects.get(username=u)
        tag = Tags(name=tagname, coder=coder)

        tag.save()
    ids = recommend_users(request.user,2)
    
    return render(request, 'base/tag.html', {'ids':ids})

@login_required(login_url='/login/')
def searchhackathon(request):
    query = request.POST.get('query', '')
    if query:
        hackathons = Hackathon.objects.filter(Q(name__icontains=query)).distinct()
    else:
        hackathons = Hackathon.objects.all()
    
    hackathon_data = []
    for hackathon in hackathons:
        organization = Organization.objects.filter(hackathons=hackathon).first()
        hackathon_data.append({
            'name': hackathon.name,
            'organization': organization.name if organization else 'Unknown'
        })
    
    return render(request, 'base/searchhackathon.html', {'hackathons': hackathon_data, 'query': query})


@login_required(login_url='/login/')
def chat_room(request):
    data = {
    "members": [
        { "id": 1, "name": "John", "image": "https://randomuser.me/api/portraits/men/1.jpg" },
        { "id": 2, "name": "Jane", "image": "https://randomuser.me/api/portraits/women/2.jpg" },
        { "id": 3, "name": "Mike", "image": "https://randomuser.me/api/portraits/men/3.jpg" },
        { "id": 4, "name": "Emily", "image": "https://randomuser.me/api/portraits/women/4.jpg" },
        { "id": 5, "name": "Chris", "image": "https://randomuser.me/api/portraits/men/5.jpg" }
    ]
    }
    return render(request, 'base/chat.html', {'data': data})

# def room(request,pk):
#     room = Room.objects.get(id=pk)
#     msgs = room.message_set.all().order_by('created')
#     participants = room.participants.all()
#     if request.method == 'POST':
#         msg = request.POST.get('body')
#         if msg != '':
#             room.message_set.create(user=request.user, body=msg)
#             room.participants.add(request.user)
#             return redirect('room', pk=room.id)

    context = {'room': room, 'msgs': msgs, 'participants': participants}
    return render(request, 'base/room.html', context)

@login_required(login_url='/login/')
def chat(request):
    user = request.user
    if request.method == 'POST':
        msg = request.POST.get('message')
        m = Chat.objects.create(sender=user, message=msg)
        m.save()
        msgs = Chat.objects.all()
    return render(request, 'base/chat.html',{'user':user, 'msg':msg})

@login_required(login_url='/login/')
def project(request):
    owner=request.user.username
    if request.method == 'POST':
        repo = request.POST.get('repo')
        owner = request.POST.get('owner')
        print(repo,owner)
        url="https://github.com/"+owner+'/'+repo
        return render(request, 'base/project.html',{'repo':url})
    return render(request, 'base/project.html')

# @login_required(login_url='/login/')
def displayorghackathons(request, hackathon_id):
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)
    teams = hackathon.teams.all()  # Fetch all the teams registered for the hackathon
    # Get details for each team
    team_details = []
    for team in teams:
        members = team.accepted_members.all()  # Get accepted members for the team
        project = Project.objects.filter(pteam=team).first()# Get the project for the team
        team_details.append({'team': team, 'members': members, 'project': project})

    return render(request, 'base/displayorghackathons.html', {'hackathon': hackathon, 'team_details': team_details})


@login_required(login_url='/login/')
def add_tag(request):
    if request.method == 'POST':
        tagname = request.POST.get('tagname', '').strip()
        if not tagname:
            messages.error(request, "Tag name cannot be empty.")
            return redirect('profile')
        
        user = request.user
        if Tags.objects.filter(name=tagname, coder=user).exists():
            messages.error(request, "Tag already exists.")
        else:
            tag = Tags(name=tagname, coder=user)
            tag.save()
            messages.success(request, "Tag added successfully!")
        
    return redirect('profile')