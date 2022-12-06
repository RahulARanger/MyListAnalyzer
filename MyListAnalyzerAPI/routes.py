from MyListAnalyzerAPI.parse_user_anime_list import parse_user_anime_list
from starlette.routing import Mount, Route


mount_route = Mount(path="/user_anime_list", name="user_details", routes=[
    Route("/process/{tab:str}", parse_user_anime_list, methods=["POST"])
])

my_list_analyzer = Mount(path="/MLA", routes=[
    mount_route
])
