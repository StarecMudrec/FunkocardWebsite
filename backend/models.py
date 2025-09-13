from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger

db = SQLAlchemy()

# Token Model
class AllowedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False)


# Token Model
class AuthToken(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(BigInteger, nullable=False)

    def __repr__(self):
        return f'<AuthToken token={self.token} user_id={self.user_id}>'

# Card Model
class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String, nullable=False, unique=True)
    img = db.Column(db.String)
    category = db.Column(db.String(20))
    name = db.Column(db.String(100))
    description = db.Column(db.String(1000))
    season_id = db.Column(db.Integer, db.ForeignKey('season.id', ondelete='CASCADE'), nullable=False)

    season = db.relationship("Season", backref=db.backref("cards"))
    comments = db.relationship('Comment', lazy=True, cascade='all, delete-orphan', back_populates='card')

    def present(self): 
        return {"id": self.id, 
                "uuid": self.uuid, 
                "season_id": self.season_id, 
                "img": self.img, 
                "category": self.category, 
                "name": self.name, 
                "description": self.description}

# Season Model
class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String(100))

    def present(self):
        return {"id": self.id, 
                "uuid": self.uuid, 
                "name": self.name}

# Comment Model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, nullable=False, unique=True)
    user_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id', ondelete='CASCADE'), nullable=False)

    card = db.relationship("Card", back_populates='comments')

    def present(self): 
        return {"id": self.id, 
                "uuid": self.uuid, 
                "user_id": self.user_id, 
                "text": self.text, 
                "card_id": self.card_id}
    
