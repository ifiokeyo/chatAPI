# Chat Application API

 > An API for a simple chat application.

## Requirements
 - Docker
 - Python3
 - Sqlite db

## Development setup

 > Clone this repo and navigate into the project's directory


#### Start up the server

```bash
$ docker-compose up --build
```

 >  The app should now be available from your browser at http://127.0.0.1:2000

 > Test API with Postman.

##### Endpoints

 > For endpoints that require authentication, add a valid access token to the Request *Authorization heade*r - *Bearer <ACCESS TOKEN>*

- **Home**

     *http://127.0.0.1:2000/*

- **Signup a user**

   POST */api/v1/auth/signup*

    > Request Payload
     
    ```
    {
        "name": <full name>,
        "username": <username>,
        "email": <email>,
        "password": <password min_length 8>  
    }
    ```

-  **Login a user**

   POST */api/v1/auth/login*

    > Request Payload 
    
    ```
    {
        "email": <email>,
        "password": <password min_length 8>  
    }
    ```

- **Logout user** `[JWT token required]`

    POST */api/v1/logout*
    
- **Create a Personal conversation** `[JWT token required]`

    POST */api/v1/conversation/personal*
    
    > The `participants` array in the request payload should only contain the user object of the other participant.
    Personal conversation require only one user object in the array. 
    
    > Request Payload 
      
    ```
    {
        "participants": [
            { "id": 2 }
        ]
    }
    ```
    
- **Create a group conversation** `[JWT token required]`

    POST */api/v1/conversation/group*
    
    > The `participants` array should only contain the user objects of other members of the group. 
     Not the creator of the chat, in this context the logged-in user.
    
    > Request Payload
    
    ```
    {
	    "group_name": "<group name>",
	    "participants": [
		    {"id": 2}, 
		    {"id": 3}
	    ]
    }
    ```
    
- **Get all users** `[JWT token required]`

    GET */api/v1/users*
    
    > This endpoint is paginated. Without the page query string, it returns results for `page 1` .
    
    > It can be modified like this: `/api/v1/users?page=2` to retrieve results for a specific page.
 
 
 - **Get a single user detail** `[JWT token required]`

    GET */api/v1/users/<user_id>*
    
    > This endpoint returns the detail of the logged-in user.
 
    
- **Send a message in a specific conversation** `[JWT token required]`

    POST */api/v1/conversation/<conversation_id>/message/send*
    
    > Request payload 
    
    ```
    {
	    "content": "<message content>"
    }
    ```
    
- **Get all messages for a specific conversation** `[JWT token required]`

    GET */api/v1/conversation/<conversation_id>/message*
    
    > User must be a participant in the conversation to access this endpoint. This endpoint is paginated. 
    Without the page query string, it returns results for `page 1` .
    
    > It can be modified like this: `/api/v1/conversation/1/message?page=2` to retrieve results for a specific page.
    

- **Retrieve a specific conversation detail** `[JWT token required]`

    GET */api/v1/conversation/<conversation_id>*
    
    > User must be a participant in the conversation to access this endpoint.

    
- **Poll all new messages after lastMessageId for a specific conversation** `[JWT token required]`

    GET */api/v1/conversation/<conversation_id>/poll/<last_message_id>*
    
    > User must be a participant in the conversation to access this endpoint.
    
    > Returns the messages that come after the id given.

    
- **Get all messages of a user for a specific conversation** `[JWT token required]`

    GET */api/v1/conversation/user/<user_id>*
    
    > User must be a participant in the conversation to access this endpoint. This endpoint is paginated. 
    Without the page query string, it returns results for `page 1` .
    
    > It can be modified like this: `/api/v1/conversation/user/1?page=2` to retrieve results for a specific page.
       
  