from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    def clone(self):
        d = dict(self.__dict__)
        if "id" in d:
            # Get rid of id
            d.pop("id")
        # Get rid of SQLAlchemy special attr
        d.pop("_sa_instance_state")
        copy = self.__class__(**d)
        return copy


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    tracks: Mapped[int] = mapped_column(nullable=True)
    artist: Mapped[str] = mapped_column(nullable=True)
    release_date: Mapped[str] = mapped_column(nullable=True)
    artwork_url: Mapped[str] = mapped_column(nullable=True)
    songs: Mapped[List["Song"]] = relationship(back_populates="album")

    def __repr__(self) -> str:
        return f"<Album= {self.title}>"

    def clone(self):
        d = dict(self.__dict__)
        if "id" in d:
            # Get rid of id
            d.pop("id")
        # Get rid of SQLAlchemy special attr
        d.pop("_sa_instance_state")
        if "songs" in d:
            d.pop("songs")
        copy = self.__class__(**d)
        return copy


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    artist: Mapped[str] = mapped_column(nullable=False)
    composer: Mapped[str] = mapped_column(nullable=True)
    genre: Mapped[str] = mapped_column(nullable=True)
    disc: Mapped[int] = mapped_column(nullable=True)
    track: Mapped[int] = mapped_column(nullable=True)
    video_id: Mapped[str] = mapped_column(nullable=False)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), nullable=False)
    album: Mapped["Album"] = relationship(back_populates="songs")

    def __repr__(self):
        return f"<Song= {self.title} by {self.artist}>"

    def clone(self):
        d = dict(self.__dict__)
        if "id" in d:
            # Get rid of id
            d.pop("id")
        # Get rid of SQLAlchemy special attr
        d.pop("_sa_instance_state")
        d["album"] = self.album.clone()
        copy = self.__class__(**d)
        return copy


class Organizer(Base):
    """
    The Organizer model is used to track an organized music collection. A row of this table must
    correspond to a song present at the organized library destination path.
    """

    __tablename__ = "organizer"

    id: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id"), nullable=False)
    org_video_id: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<Organized Song= {self.id} with org video id {self.org_video_id}"
