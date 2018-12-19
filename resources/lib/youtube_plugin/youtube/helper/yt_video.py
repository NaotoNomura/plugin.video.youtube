# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtube)
    Copyright (C) 2016-2018 plugin.video.youtube

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only for more information.
"""

import re

import xbmc

from ... import kodion
from ...youtube.helper import v3


def _process_rate_video(provider, context, re_match):
    ratings = ['like', 'dislike', 'none']

    rating_param = context.get_param('rating', '')
    if rating_param:
        rating_param = rating_param.lower()

    video_id = context.get_param('video_id', '')
    if not video_id:
        try:
            video_id = re_match.group('video_id')
        except IndexError:
            if rating_param in ratings:
                listitem_path = xbmc.getInfoLabel('Container.ListItem(0).FileNameAndPath')
                if listitem_path.startswith('plugin://%s/play/' % context._plugin_id):
                    match = re.search(r'.*video_id=(?P<video_id>[a-zA-Z0-9_\-]{11}).*', listitem_path)
                    if match:
                        video_id = match.group('video_id')

            if not video_id:
                raise kodion.KodionException('video/rate/: missing video_id')

            if not rating_param:
                raise kodion.KodionException('video/rate/: missing rating')

    try:
        current_rating = re_match.group('rating')
    except IndexError:
        current_rating = None

    if not current_rating:
        client = provider.get_client(context)
        json_data = client.get_video_rating(video_id)
        if not v3.handle_error(provider, context, json_data):
            return False

        items = json_data.get('items', [])
        if items:
            current_rating = items[0].get('rating', '')

    rating_items = []
    if not rating_param:
        for rating in ratings:
            if rating != current_rating:
                rating_items.append((context.localize(provider.LOCAL_MAP['youtube.video.rate.%s' % rating]), rating))
        result = context.get_ui().on_select(context.localize(provider.LOCAL_MAP['youtube.video.rate']), rating_items)
    else:
        if rating_param != current_rating:
            result = rating_param
        else:
            result = -1

    if result != -1:
        client = provider.get_client(context).rate_video(video_id, result)

        # this will be set if we are in the 'Liked Video' playlist
        if context.get_param('refresh_container', '0') == '1':
            context.get_ui().refresh_container()


def _process_more_for_video(provider, context, re_match):
    video_id = context.get_param('video_id', '')
    if not video_id:
        raise kodion.KodionException('video/more/: missing video_id')

    items = []

    is_logged_in = context.get_param('logged_in', '0')
    if is_logged_in == '1':
        # add video to a playlist
        items.append((context.localize(provider.LOCAL_MAP['youtube.video.add_to_playlist']),
                      'RunPlugin(%s)' % context.create_uri(['playlist', 'select', 'playlist'], {'video_id': video_id})))

    # default items
    items.extend([(context.localize(provider.LOCAL_MAP['youtube.related_videos']),
                   'Container.Update(%s)' % context.create_uri(['special', 'related_videos'], {'video_id': video_id})),
                  (context.localize(provider.LOCAL_MAP['youtube.video.description.links']),
                   'Container.Update(%s)' % context.create_uri(['special', 'description_links'],
                                                               {'video_id': video_id}))])

    if is_logged_in == '1':
        # rate a video
        refresh_container = context.get_param('refresh_container', '0')
        items.append((context.localize(provider.LOCAL_MAP['youtube.video.rate']),
                      'RunPlugin(%s)' % context.create_uri(['video', 'rate'], {'video_id': video_id,
                                                                               'refresh_container': refresh_container})))

    result = context.get_ui().on_select(context.localize(provider.LOCAL_MAP['youtube.video.more']), items)
    if result != -1:
        context.execute(result)


def process(method, provider, context, re_match):
    if method == 'rate':
        return _process_rate_video(provider, context, re_match)
    elif method == 'more':
        return _process_more_for_video(provider, context, re_match)
    else:
        raise kodion.KodionException("Unknown method '%s'" % method)

    return True
