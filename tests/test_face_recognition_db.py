import json
import os

import pytest

from src.vision.face_recognition_db import FaceRecognitionDB


@pytest.fixture
def face_db(tmp_path):
    return FaceRecognitionDB(tmp_path)


def _vector(*values, dim=512):
    vals = [float(x) for x in values]
    return vals + [0.0] * (dim - len(vals))


def _write_embeddings(face_db, entries):
    face_db.embedding_dir.mkdir(parents=True, exist_ok=True)
    face_db.embedding_file.write_text(
        json.dumps({'students': entries}, ensure_ascii=False), encoding='utf-8'
    )


class TestCosineSimilarity:
    def test_identity_vector(self, face_db):
        v = _vector(1.0, 0.0, 0.0)
        assert face_db._cosine_similarity(v, v) == 1.0

    def test_orthogonal_vectors(self, face_db):
        assert face_db._cosine_similarity(
            _vector(1.0, 0.0), _vector(0.0, 1.0)
        ) == 0.0

    def test_opposite_vectors(self, face_db):
        assert face_db._cosine_similarity(
            _vector(1.0, 0.0), _vector(-1.0, 0.0)
        ) == -1.0

    def test_zero_vector(self, face_db):
        assert face_db._cosine_similarity(
            _vector(1.0, 0.0), _vector(0.0, 0.0)
        ) == 0.0


class TestMatchEmbedding:
    def test_matches_above_threshold(self, face_db):
        query = _vector(1.0, 0.0)
        _write_embeddings(face_db, [
            {'label': '\u5b78\u751f1', 'embedding': _vector(0.9, 0.1)},
            {'label': '\u5b78\u751f2', 'embedding': _vector(0.1, 0.9)},
        ])
        result = face_db.match_embedding(query, threshold=0.7)
        assert len(result) == 1
        assert result[0]['label'] == '\u5b78\u751f1'

    def test_empty_below_threshold(self, face_db):
        query = _vector(1.0, 0.0)
        _write_embeddings(face_db, [
            {'label': '\u5b78\u751f1', 'embedding': _vector(0.0, 1.0)},
        ])
        result = face_db.match_embedding(query, threshold=0.5)
        assert result == []

    def test_sorted_by_similarity_descending(self, face_db):
        query = _vector(1.0, 0.0)
        _write_embeddings(face_db, [
            {'label': '\u5b78\u751f1', 'embedding': _vector(0.9, 0.1)},
            {'label': '\u5b78\u751f2', 'embedding': _vector(0.5, 0.5)},
            {'label': '\u5b78\u751f3', 'embedding': _vector(0.99, 0.01)},
        ])
        result = face_db.match_embedding(query, threshold=0.4)
        assert [r['label'] for r in result] == [
            '\u5b78\u751f3', '\u5b78\u751f1', '\u5b78\u751f2'
        ]


class TestLoadDatabase:
    def test_file_missing_returns_empty(self, face_db):
        assert face_db.load_database() == []

    def test_file_exists_returns_list(self, face_db):
        _write_embeddings(face_db, [
            {'label': '\u5b78\u751f1', 'embedding': _vector(1.0, 0.0)},
        ])
        result = face_db.load_database()
        assert len(result) == 1
        assert result[0]['label'] == '\u5b78\u751f1'

    def test_cache_hit_returns_same_object(self, face_db):
        _write_embeddings(face_db, [
            {'label': '\u5b78\u751f1', 'embedding': _vector(1.0, 0.0)},
        ])
        first = face_db.load_database()
        second = face_db.load_database()
        assert first is second

    def test_cache_invalidated_on_mtime_change(self, face_db):
        _write_embeddings(face_db, [
            {'label': '\u5b78\u751f1', 'embedding': _vector(1.0, 0.0)},
        ])
        first = face_db.load_database()
        _write_embeddings(face_db, [
            {'label': '\u5b78\u751f2', 'embedding': _vector(0.0, 1.0)},
        ])
        os.utime(face_db.embedding_file,
                 (face_db.embedding_file.stat().st_mtime + 1,) * 2)
        second = face_db.load_database()
        assert first is not second
        assert second[0]['label'] == '\u5b78\u751f2'


class TestSanitizeProfileLabel:
    def test_normal_name(self, face_db):
        assert face_db._sanitize_profile_label('John Doe') == 'John Doe'

    def test_empty_name_falls_back_to_student_id(self, face_db):
        assert face_db._sanitize_profile_label('', student_id='123') == '123'

    def test_both_empty_calls_next_student_label(self, face_db):
        label = face_db._sanitize_profile_label('', '')
        assert label == '\u5b78\u751f1'


class TestResolveProfileLabel:
    def test_matches_by_student_id(self, face_db):
        profiles = {
            '\u5b78\u751f1': {'student_id': '001', 'name': 'Alice'},
        }
        label, desired = face_db._resolve_profile_label(
            profiles, '001', 'Alice'
        )
        assert label == '\u5b78\u751f1'
        assert desired == 'Alice'

    def test_matches_by_name(self, face_db):
        profiles = {
            '\u5b78\u751f1': {'student_id': '001', 'name': 'Alice'},
        }
        label, desired = face_db._resolve_profile_label(
            profiles, '', 'Alice'
        )
        assert label == '\u5b78\u751f1'
        assert desired == 'Alice'

    def test_no_match_returns_none_and_desired(self, face_db):
        label, desired = face_db._resolve_profile_label({}, '999', 'Bob')
        assert label is None
        assert desired == 'Bob'


class TestTemporaryLabel:
    def test_prefix_returns_chinese_string(self, face_db):
        assert face_db._temporary_label_prefix() == '\u5b78\u751f'

    def test_starts_with_prefix_is_temporary(self, face_db):
        assert face_db._is_temporary_label('\u5b78\u751f1')
        assert face_db._is_temporary_label('\u5b78\u751f42')

    def test_other_label_is_not_temporary(self, face_db):
        assert not face_db._is_temporary_label('John Doe')
        assert not face_db._is_temporary_label('')
        assert not face_db._is_temporary_label(None)


class TestEnsureStorage:
    def test_creates_directories(self, face_db):
        face_db.ensure_storage()
        assert face_db.photo_root.is_dir()
        assert face_db.embedding_dir.is_dir()


class TestListStudentLabels:
    def test_returns_sorted_dir_names(self, face_db):
        face_db.get_photo_root()
        (face_db.photo_root / '\u5b78\u751f2').mkdir()
        (face_db.photo_root / '\u5b78\u751f1').mkdir()
        (face_db.photo_root / '\u5b78\u751f10').mkdir()
        assert face_db.list_student_labels() == [
            '\u5b78\u751f1', '\u5b78\u751f10', '\u5b78\u751f2'
        ]


class TestUserProfiles:
    def test_round_trip(self, face_db):
        face_db.get_photo_root()
        (face_db.photo_root / '\u5b78\u751f1').mkdir()
        profiles = {
            '\u5b78\u751f1': {
                'label': '\u5b78\u751f1',
                'name': 'Alice',
                'student_id': '001',
            },
        }
        face_db.save_user_profiles(profiles)
        loaded = face_db.load_user_profiles()
        assert loaded['\u5b78\u751f1']['name'] == 'Alice'
        assert loaded['\u5b78\u751f1']['student_id'] == '001'


class TestSaveTrainingImage:
    def test_unknown_label_raises(self, face_db):
        face_db.ensure_storage()
        with pytest.raises(RuntimeError, match='Unknown student label'):
            face_db.save_training_image('\u4e0d\u5b58\u5728', 'test.jpg',
                                        b'fake_image_data')

    def test_saves_file_with_proper_label(self, face_db):
        face_db.get_photo_root()
        (face_db.photo_root / '\u5b78\u751f1').mkdir()
        result = face_db.save_training_image(
            '\u5b78\u751f1', 'test.jpg', b'fake_image_data'
        )
        assert result.name == '01.jpg'
        assert result.read_bytes() == b'fake_image_data'
