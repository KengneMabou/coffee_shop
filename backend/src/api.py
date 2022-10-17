import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
    Implement endpoint GET /drinks
    it should be a public endpoint
    it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks")
def retrieve_drinks():

    all_drinks = Drink.query.order_by(Drink.id).all()

    if len(all_drinks) == 0:
        abort(404)

    formatted_drinks = [c_drink.short() for c_drink in all_drinks]

    return jsonify(
        {"success": True, "drinks": formatted_drinks}
    )

'''
    Implement endpoint GET /drinks-detail
    it should require the 'get:drinks-detail' permission
    it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks-detail")
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt_payload):

    all_drinks = Drink.query.order_by(Drink.id).all()

    if len(all_drinks) == 0:
        abort(404)

    formatted_drinks = [c_drink.long() for c_drink in all_drinks]

    return jsonify(
        {"success": True, "drinks": formatted_drinks}
    )


'''
    Implement endpoint POST /drinks
    it should create a new row in the drinks table
    it should require the 'post:drinks' permission
    it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks", methods=["POST"])
@requires_auth('post:drinks')
def create_drink(jwt_payload):
    body = request.get_json()

    new_title = body.get("title", None)
    new_recipe = json.dumps(body.get("recipe", None))

    try:
        drink = Drink(title=new_title, recipe=new_recipe,)

        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })

    except:
        abort(422)

'''
    Implement endpoint PATCH /drinks/<id> where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should update the corresponding row for <id>
    it should require the 'patch:drinks' permission
    it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth('patch:drinks')
def modify_drink(jwt_payload, drink_id):
    not_found = False
    try:
        drink_obj = Drink.query.filter(Drink.id == drink_id).one_or_none()

        if drink_obj is None:
            not_found = True
            raise Exception("Not found")
        else:
            body = request.get_json()
            new_title = body.get("title", None)
            new_recipe = body.get("recipe", None)
            if new_title:
                drink_obj.title = new_title
            if new_recipe:
                new_recipe = json.dumps(new_recipe)
                drink_obj.recipe = new_recipe
            drink_obj.update()

        return jsonify(
            {
                "success": True,
                "drinks": [drink_obj.long()]
            }
        )

    except:
        if not_found:
            abort(404)
        abort(422)

'''
    Implement endpoint DELETE /drinks/<id> where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should delete the corresponding row for <id>
    it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drink(jwt_payload, drink_id):
    not_found = False
    try:
        drink_obj = Drink.query.filter(Drink.id == drink_id).one_or_none()

        if drink_obj is None:
            not_found = True
            raise Exception("Not found")

        drink_obj.delete()

        return jsonify(
            {
                "success": True,
                "delete": drink_id,
            }
        )

    except:
        if not_found:
            abort(404)
        abort(422)

# Error Handling

'''
    implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "resource not found"}),
        404,
    )


@app.errorhandler(422)
def unprocessable(error):
    return (
        jsonify({"success": False, "error": 422, "message": "unprocessable"}),
        422,
    )


@app.errorhandler(405)
def not_found(error):
    return (
        jsonify({"success": False, "error": 405, "message": "method not allowed"}),
        405,
    )


@app.errorhandler(500)
def internal_server_error(error):
    return (
        jsonify({"success": False, "error": 500, "message": "Internal server error"}), 500,
    )


'''
    implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(400)
def bad_request(error):
    if isinstance(error.description,dict) and 'code' in error.description and \
            'description' in error.description:
        return (
            jsonify({"success": False, "error": 400,
                     "message": "%s : %s" % (error.description['code'], error.description['description'])
                     }), 400,
        )

    return (jsonify({"success": False, "error": 400,
                     "message": "bad request"}), 400,
            )


@app.errorhandler(401)
def unauthorized(error):
    if isinstance(error.description, dict) and 'code' in error.description and \
            'description' in error.description:
        return (
            jsonify({"success": False, "error": 401,
                     "message": "%s : %s" % (error.description['code'], error.description['description'])
                     }), 401,
        )

    return (
        jsonify({"success": False, "error": 401,
                 "message": "Unauthorized"
                 }), 401,
    )


@app.errorhandler(403)
def forbidden(error):
    if isinstance(error.description, dict) and 'code' in error.description and \
            'description' in error.description:
        return (
            jsonify({"success": False, "error": 403,
                     "message": "%s : %s" % (error.description['code'], error.description['description'])
                     }), 403,
        )

    return (
        jsonify({"success": False, "error": 403, "message": "Forbidden"}), 403,
    )

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    """
    Receive the raised authorization error and propagates it as response
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

