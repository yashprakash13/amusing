from typing import List

from sqlalchemy import ForeignKey, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    songs: Mapped[List["Song"]] = relationship(back_populates="album")

    def __repr__(self) -> str:
        return f"<Album= {self.name}>"


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int] = mapped_column(nullable=False)
    artist: Mapped[str]
    video_id: Mapped[str]
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), nullable=False)
    album: Mapped["Album"] = relationship(back_populates="songs")

    def __repr__(self):
        return f"<Song= {self.name} by {self.artist}>"
