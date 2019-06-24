from typing import NamedTuple
from typeit import type_constructor


class AuthenticatedUser(NamedTuple):
    """
    https://developer.github.com/v3/users/#response-with-public-profile-information
    """
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool
    name: str
    company: str
    blog: str
    location: str
    email: str
    hireable: bool
    bio: str
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: str
    updated_at: str


MakeAuthenticatedUser = type_constructor ^ AuthenticatedUser
