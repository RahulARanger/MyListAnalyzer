from MyListAnalyzerAPI.user_details import parse_user_details, HandleProcessUserDetails
from starlette.middleware import Middleware
from starlette.routing import Mount, Route


mount_route = Mount(path="/user_details", name="user_details", routes=[
    Route("/process/{tab:int}", parse_user_details, methods=["POST"])
], middleware=[Middleware(HandleProcessUserDetails)])

my_list_analyzer = Mount(path="/MLA", routes=[
    mount_route
])
