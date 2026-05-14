"""Tests for MinerU markdown enrichment from content_list sidecars."""

import json

from app.services.infra.mineru_client import (
    apply_asset_urls_to_markdown,
    enrich_markdown_with_content_list_images,
)


def test_enrich_appends_images_when_full_md_has_no_refs():
    md = '# Title\n\nHello world.\n'
    cl = [
        {'type': 'text', 'text': 'Hello', 'page_idx': 0},
        {
            'type': 'image',
            'img_path': 'images/aaa.jpg',
            'image_caption': [],
            'page_idx': 0,
        },
    ]
    files = [
        ('other/full.md', b'x'),
        ('p_content_list.json', json.dumps(cl).encode('utf-8')),
    ]
    out = enrich_markdown_with_content_list_images(md, files)
    assert '![](images/aaa.jpg)' in out
    assert 'Hello world' in out


def test_enrich_skips_when_markdown_already_has_image():
    md = '![](images/aaa.jpg)\n'
    cl = [{'type': 'image', 'img_path': 'images/aaa.jpg', 'page_idx': 0}]
    files = [('x_content_list.json', json.dumps(cl).encode('utf-8'))]
    out = enrich_markdown_with_content_list_images(md, files)
    assert out.count('![](images/aaa.jpg)') == 1


def test_enrich_prefers_v2_when_it_has_paths():
    v1 = [{'type': 'image', 'img_path': 'images/from_v1.jpg', 'page_idx': 0}]
    v2 = [
        [
            {
                'type': 'image',
                'content': {
                    'image_source': {'path': 'images/from_v2.jpg'},
                },
                'bbox': [0, 0, 1, 1],
            },
        ],
    ]
    files = [
        ('a_content_list.json', json.dumps(v1).encode('utf-8')),
        ('a_content_list_v2.json', json.dumps(v2).encode('utf-8')),
    ]
    md = 'text only\n'
    out = enrich_markdown_with_content_list_images(md, files)
    assert 'from_v2.jpg' in out
    assert 'from_v1.jpg' not in out


def test_apply_urls_after_enrich_rewrites_appended_paths():
    md = '# x\n'
    cl = [{'type': 'image', 'img_path': 'images/x.jpg', 'page_idx': 0}]
    files = [('z_content_list.json', json.dumps(cl).encode('utf-8'))]
    enriched = enrich_markdown_with_content_list_images(md, files)
    urls = {'images/x.jpg': 'https://cdn.example/img/x.jpg'}
    final = apply_asset_urls_to_markdown(enriched, urls)
    assert 'https://cdn.example/img/x.jpg' in final
    assert 'images/x.jpg' not in final


def test_apply_urls_does_not_corrupt_url_when_key_is_substring_of_url():
    """Regression: global str.replace rewrote ``images/...`` inside COS URLs."""
    md = '![](images/abc.jpg)\n'
    cos = (
        'https://bucket.cos.region.myqcloud.com/notebooks/sources/parsed/'
        'src-id/images/abc.jpg?q-sign-algorithm=sha1'
    )
    out = apply_asset_urls_to_markdown(md, {'images/abc.jpg': cos})
    assert out.count('https://bucket.cos.region.myqcloud.com') == 1
    assert f'![]({cos})' in out
