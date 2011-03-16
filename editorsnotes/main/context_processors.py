from models import Project

def list_projects(request):
	projects = Project.objects.all()
	return {'list_projects': projects}
