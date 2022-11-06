from sanic.blueprint_group import BlueprintGroup
from MyListAnalyzerAPI.user_details import blue_print as user_details


my_list_analyzer = BlueprintGroup(url_prefix="/MLA")
my_list_analyzer.append(user_details)




