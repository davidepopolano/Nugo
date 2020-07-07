import mysql.connector
import constants
from constants import LOGGER


def get_db_connection(user, password, host, database_name):

    """
        :param user:
        :param password:
        :param host:
        :param database_name:
        :return: returns a connection to the db, note that it needs to be closed
    """

    try:
        return mysql.connector.connect(user=user, password=password, host=host, database=database_name)
    except Exception as e:
        LOGGER.error("Error while creating database connection {}" .format(e))
        


def insert_personal_data(profile_link, personal_data):
    """
        :param profile_link: link to profile no standard prefix
        :param personal_data: {
                                    "sex": 1 if male 0 if female "NULL" if not known,
                                    "cityName": "...",
                                    "contacts": [
                                                    {
                                                        "contact": "......",
                                                        "type": "EMAIL"/"NUMBER"
                                                    }
                                                ]
                                    "jobs": ["..."]
                              }
    """
    connection = None

    try:
        connection = get_db_connection(constants.DB_USER, constants.DB_PASSWORD, constants.DB_HOST, constants.DB_NAME)
        cursor = connection.cursor()

        user_id = get_user_id_from_link(profile_link, cursor)

        if personal_data["cityName"] != "NULL":

            city_id = insert_city(
                                    personal_data["cityName"].replace("'", " "),
                                    cursor,
                                    connection
                                 )
        else:
            city_id = "NULL"

        update_user_query = "UPDATE user SET alreadyVisited = 1 , sex = {} , idCurrentCity = {} WHERE idUser = {}"\
                    .format(personal_data["sex"],
                    city_id,
                    user_id)

        cursor.execute(update_user_query)

        for contact in personal_data["contacts"]:

            insert_contact(user_id, contact.replace("'", " "), cursor, connection)

        for job in personal_data["jobs"]:
            insert_job(user_id, job.replace("'", " "), cursor, connection)


        connection.commit()

    except Exception as e:

        connection.rollback()
        LOGGER.error("Error while inserting personal data error: {}".format(e))

    finally:
        connection.close()


def get_users_not_visited():
    """
        :return: list of the profile's link of the users we haven't visited yet (the usual facebook prefix is omitted)
    """
    connection = None

    try:
        connection = get_db_connection(constants.DB_USER, constants.DB_PASSWORD, constants.DB_HOST, constants.DB_NAME)
        cursor = connection.cursor()

        cursor.execute("SELECT linkToProfile FROM user WHERE alreadyVisited = 0")

        return cursor.fetchall()

    except Exception as e:
        LOGGER.error("Error while retrieving users not visited: {}".format(e))
    finally:
        connection.close()


def insert_post(post):

    """
        :param post: dict defined as follows:
                {
                    postText: "....",
                    comments: [{...},{...},ecc] -> every comment is a dict composed as follows
                                                   {
                                                        "author": "...",
                                                        "text": "..."
                                                        "linkToProfile": "..." link to facebook profile without standard
                                                                               prefix https://www.facebook.com
                                                   }
                    location: "..."
                }
        function:Inserts the post passed as argument in the database
    """

    connection = None
    post["postText"] = post["postText"].replace("'", " ")
    try:
        connection = get_db_connection(constants.DB_USER, constants.DB_PASSWORD, constants.DB_HOST, constants.DB_NAME)
        cursor = connection.cursor()

        post_query = "INSERT INTO post (postText, postSentiment, idOfMentionedLocation) " \
                     "values ('{}',{},{})"

        location_id = insert_location(post["location"].replace("'", " "), cursor, connection)

        if location_id is None:
            cursor.execute(post_query.format(
                post["postText"].replace("'", " "),
                "NULL",  # TODO Sentiment
                "NULL"
            ))
        else:
            cursor.execute(post_query.format(
                post["postText"].replace("'", " "),
                "NULL",  # TODO Sentiment
                location_id
            ))

        post_id = cursor.lastrowid

        comment_query = "INSERT INTO comment (commentText, commentSentiment, idOfPost, idOfAuthor) " \
                        "values ('{}',{},{},{})"

        for comment in post["comments"]:

            author = comment["author"].replace("'", " ")
            text = comment["text"].replace("'", " ")
            link = comment["linkToProfile"]

            if ".php" not in link:
                cursor.execute(comment_query.format(
                                                    text,
                                                    "NULL",  # TODO Sentiment
                                                    post_id,
                                                    insert_user(author, link, cursor, connection)
                                                ))

        connection.commit()

        LOGGER.debug("Post inserted correctly")

    except Exception as e:

        connection.rollback()
        LOGGER.error("Error while inserting post: {}".format(e))

    finally:
        connection.close()


def insert_location(location, cursor, connection):

    """
        :param location: location name as string
        :param cursor: database cursor
        :param connection: database connection
        :return: inserted location's id both if already present or not
    """

    if location == "NULL":
        return None

    try:

        cursor.execute("INSERT INTO location (locationName) values ('{}')".format(location))
        connection.commit()

        location_id = cursor.lastrowid


        LOGGER.debug("Location {} inserted correctly, returning associated id ".format(location_id))


        return cursor.lastrowid

    except mysql.connector.IntegrityError:

        cursor.execute("SELECT idLocation FROM location WHERE locationName = '{}'".format(location))
        location_id = cursor.fetchone()[0]


        LOGGER.debug("Location {} already present, returning associated id {}".format(location, location_id))


        return location_id


def insert_user(author, link, cursor, connection):

    """
        :param author: username
        :param link: link to facebook profile without standard prefix https://www.facebook.com
        :param cursor: database cursor
        :param connection: database connection
        :return: inserted user's id both if already present or not
    """

    try:

        cursor.execute("INSERT INTO user (username, linkToProfile, alreadyVisited, sex, idCurrentCity) " +
                       "values ('{}','{}', 0, NULL, NULL)".format(author, link))
        connection.commit()

        user_id = cursor.lastrowid

        LOGGER.debug("User {} inserted correctly, returning associated id {}".format(author, user_id))

        return cursor.lastrowid

    except mysql.connector.IntegrityError:

        cursor.execute("SELECT idUser FROM user WHERE linkToProfile = '{}'".format(link))

        user_id = cursor.fetchone()[0]

        LOGGER.debug("User {} already present, returning associated id {} ".format(author, user_id))

        return user_id


def insert_city(name, cursor, connection):

    """
        :param name: cityName
        :param cursor: database cursor
        :param connection: database connection
        :return: inserted city's id both if already present or not
    """

    try:

        cursor.execute("INSERT INTO city (cityName) " +
                       "values ('{}')".format(name))
        connection.commit()

        city_id = cursor.lastrowid

        LOGGER.debug("City {} inserted correctly, returning associated id {}".format(name, city_id))

        return city_id

    except mysql.connector.IntegrityError:

        cursor.execute("SELECT idCity FROM City WHERE cityName = '{}'".format(name))
        city_id = cursor.fetchone()[0]

        LOGGER.debug("City {} already present, returning associated id {}".format(name, city_id))

        return city_id


def get_user_id_from_link(link, cursor):
    """
        :param link:  linkToProfile no prefix
        :param cursor: database cursor
        :return: user id
    """
    try:

        cursor.execute("SELECT idUser FROM user WHERE linkToProfile = '{}'".format(link))
        user_id = cursor.fetchone()[0]

        LOGGER.debug("User {} returning associated id ".format(link, user_id))

        return user_id


        user_id = cursor.fetchone()[0]

        LOGGER.debug("User {} already present, returning associated id {} ".format(author, user_id))

        return user_id

    except Exception as e:

        LOGGER.error("Error while getting id of user: {} error: {}".format(link, e))


def insert_contact(user_id, contact, cursor, connection):
    """
        :param user_id:
        :param contact:  {
                            "contact": "......",
                            "type": "EMAIL" / "NUMBER" / "ecc"
                         }
        :param connection: database connection
        :param cursor: database cursor
    """

    try:

        cursor.execute("INSERT INTO contact (contact,idOfContactType) " +
                       "values ('{}','{}')".format(
                                                    contact["contact"],
                                                    get_id_of_contact_type(contact["type"], cursor, connection)
                                                  ))

        contact_id = cursor.lastrowid

        cursor.execute("INSERT INTO usercontacts (idContact,idUser) values ({},{})".format(contact_id, user_id))

        LOGGER.debug("contact inserted correctly, returning associated id {}".format(contact_id))
        connection.commit()

    except Exception as e:

        LOGGER.error("Error while inserting contact of user {} error {}".format(user_id, e))


def get_id_of_contact_type(contact_type, cursor, connection):
    """
        :param contact_type: contact type
        :param cursor: database cursor
        :param connection: connection cursor
        :return: id of contact type if found, creates one and returns it if not found
    """

    try:

        cursor.execute("SELECT idContactType FROM contacttype WHERE contactType = '{}'".format(contact_type.upper()))
        contact_type_id = cursor.fetchone()[0]

        LOGGER.debug("returning id of contact type: {}".format(contact_type))

        return contact_type_id

    except Exception as e:

        cursor.execute("INSERT INTO contacttype (contactType) " +
                       "values ('{}')".format(contact_type))
        connection.commit()

        contact_type_id = cursor.lastrowid

        LOGGER.debug("Contact type {} created correctly, returning associated id {}".format(contact_type
                                                                                            , contact_type_id))

        return contact_type_id


def insert_job(user_id, job, cursor, connection):

    """
        :param user_id:
        :param job:
        :param cursor:
        :param connection:
    """

    try:

        cursor.execute("INSERT INTO job (jobName) " +
                       "values ('{}')".format(job))

        job_id = cursor.lastrowid

        cursor.execute("INSERT INTO userjob (idUser,idJob) values ({},{})".format(user_id, job_id))

        LOGGER.debug("job inserted correctly")

    except Exception as e:

        LOGGER.error("Error while inserting job of user {} error {}".format(user_id, e))


def test_connection():

    LOGGER.debug("Testing db connection")

    connection = get_db_connection(constants.DB_USER, constants.DB_PASSWORD, constants.DB_HOST, constants.DB_NAME)
    connection.close()

    LOGGER.debug("Connection established successfully")


if __name__ == "__main__":
    test_connection()
