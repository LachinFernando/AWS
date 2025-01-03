import json
import hashlib
import boto3


client = boto3.client('dynamodb')
table_name = 'ibs-users'


def password_hash(password: str) -> str:

    return hashlib.md5(password.encode("utf-8")).hexdigest()


def db_put_item(user_name: str, password: str):
  data = client.put_item(
    TableName=table_name,
    Item={
        'user_id': {
          'S': user_name
        },
        'password': {
          'S': password_hash(password)
        },
    }
  )


def get_user_details(username: str):
  data = client.query(
    ExpressionAttributeValues={
        ':input_username': {
            'S': username,
        },
    },
    KeyConditionExpression='user_id = :input_username',
    TableName=table_name
  )
  return data


def process_get_request(event):
  params = event["queryStringParameters"]
  username = params["username"]
  password = params["password"]

  # get user details
  user_data = get_user_details(username)
  if user_data["Count"] == 0:
    return {
      "status": "failure",
      "data": "",
      "errors": ["Invalid Username!"]
    }
  # input password
  hash_input_password = password_hash(password)
  # user password
  original_password = user_data["Items"][0]["password"]["S"]

  if hash_input_password == original_password:
    return {
      "status": "success",
      "data": {"logIn": True},
      "errors": [None]
    }
  else:
    return {
      "status": "failure",
      "data": "",
      "errors": ["Incorrect Password!"]
    }


def process_post_request(event):
  params = event["body"]
  username = params["username"]
  password = params["password"]

  # get particular user details
  user_data = get_user_details(username)
  print(user_data)
  if user_data["Count"] != 0:
    return {
      "status": "failure",
      "data": "",
      "errors": ["User already Exists! Please try another email."]
    }

  # insert the values
  try:
    insert_response = db_put_item(username, password)

    return {
      "status": "success",
      "data": {"username": username},
      "errors": [None]
    }
  except Exception as error:
    message = "Cannot insert values to database: Error: {}".format(str(error))
    return {
      "status": "failure",
      "data": "",
      "errors": ["Cannot Insert Values to the Database"]
    }

def lambda_handler(event, context):
    print(event)
    try:
        if event["httpMethod"] == "POST":
            response = process_post_request(event)
            return response
        elif event["httpMethod"] == "GET":
            response = process_get_request(event)
            return response
        else:
            print('Unsupported Method: {}'.format(event['httpMethod']))
            return {
                "status": "Failure",
                "data": "",
                "errors": ["Unsupported Method"]
            }
    except Exception as error:
        message = "unsupported method: error: {}".format(str(error))
        print(message)
        return {
            "status": "Failure",
            "data": "",
            "errors": ["Unsupported Method"]
        }
