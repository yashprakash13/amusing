from typing import List

from sqlalchemy import ForeignKey, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    tracks: Mapped[int] = mapped_column(nullable=True)
    artist: Mapped[str] = mapped_column(nullable=True)
    release_date: Mapped[str] = mapped_column(nullable=True)
    songs: Mapped[List["Song"]] = relationship(back_populates="album")

    def __repr__(self) -> str:
        return f"<Album= {self.title}>"


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    artist: Mapped[str] = mapped_column(nullable=False)
    composer: Mapped[str] = mapped_column(nullable=True)
    genre: Mapped[str] = mapped_column(nullable=True)
    track: Mapped[int] = mapped_column(nullable=True)
    video_id: Mapped[str] = mapped_column(nullable=False)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), nullable=False)
    album: Mapped["Album"] = relationship(back_populates="songs")

    def __repr__(self):
        return f"<Song= {self.title} by {self.artist}>"
