#!/usr/bin/env python3
"""Create Dropbox shared link"""

import sys
import json
import requests

TOKEN = "sl.u.AGQ5Vi859zcb-6yAe4tpVRoicundeH5SGCE8RglqgcdfNZ6mTFY8q6qCdI8aeP4ceI0sAtV8rAusSf6ybY0qRPnW9DlGgibKIX1Fu8b7jqqiw6oydAr_RsZ_EU1s-t3S8QUE0o2PT0BROrdSgxMl1Z1L4O73OJJRCIgGA4d_xRRK2gm9v03zAHd_aYfh2JQaazEPM63LVaMBbd4h13k1NyGW1bK54kAeKUkdoBuHQo91t5HUWVZoRyu162CrmNBcuepVr3UvxZP_nxKtrAAPSxemWv-rswZchl3mg8Cu27Sv5PD7dou_rIQL50P329HlF043tJxV5WMkHxBjlbaFyXEEK7pueOJ752BHbviLGa0EArnRc3Ys8GN1RA7-tpNeWIH924u_iqQidRsI8r_px9rysznrYgQggeux4alViqe85LesaXicA6DmGGFgTNlIR934FA6AvoXYJ0UIJGJXE7SkatVXfvsa6BFC9B7S9wsygc6rYzH6sqsLP2oH_LZTQ56x-0R8Wh0ylHz50Gzd-BSKTye99MIUukFGTQ_yAK43aW-O99hiJoFTus9R07hmxFiSHpFk5stplus7FA2oFc9gr1Ph9g52HkJZXERMuALQtJpSGDcvMns37aHpjuhkYNXPsvIVr95ySneoQhPk28CCPI2T9sWpxN_AZHgvU19Muj8DTLrbKqKl5D7w130JQoOBMBkvVtrkEaFdyRnrjQCIM86CgJS8ZxGt9C1nHDeJ394VJRYw6UQk-qLh9Mh0nIfG5qMf7AG2ewqw7dnMb5ahYMM0G-4B6sHiU5EuCBCFUP5wl5ES5bRRdO7CPGgVXMglL0e_H_yKAI5RBvpG-JsmrjVD1xVuPtWeCRlbHY8OwZF7xicuR1bXcVvVxhN4Fxe1fnddmC5F3XUBoKFhC3m0MfNw_ejtN652iKr-WQ9uU5j1_W20K26Muc-bW0Hi7z7pQvriQ_LXB3pj6InaueEyHi4n1WHuokLH6P9c5Hjl5dm34GwwmTpNHoa5go9KNEYn4sRUhBSas9zIvfGA_vH51zPrGaWorPPDjotClrJidyi67AXq7sXmqSqEYPKkN0QyTODnraCdQbcAIfiqexYZ1BafdbJsfjRov0g22StVhPaYjXrgL04rwC1EXGQG2MSnz6BrBERXNfaUlv180G_BJPRuYTnDRq9bPa68ALmcyobRihjHLDdkFEFIjWVKQ2aDlwn4g7-5yjjIkPh68GUTHDW6905njTymliN4NDGAIrlEOH0pCGoCob32_tTb9z7uyHSZ5VR5N2ky4cNm6MZ7WY0QMoStP0z6-6Gd8l-S_ZLXtXNL68smJ7sl0T9CWZWJ3mOQgnrHonOWuc36NaNz62JWFMmMZ_1iG32kfQq0mScadTrP2ZFE-NSnaLkWMFhXWcLssHjCB_50nzCXaCXV"

def create_shared_link(path, read_only=True):
    """Create a shared link for a file or folder"""
    url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
    
    settings = {
        "requested_visibility": "public",
        "audience": "public",
        "access": "viewer" if read_only else "editor"
    }
    
    data = {
        "path": path,
        "settings": settings
    }
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        url = result.get('url', '')
        print(f"✅ Shareable link created:")
        print(f"   {url}")
        return url
    elif response.status_code == 409:
        # Link already exists, get it
        error_data = response.json()
        if 'shared_link_already_exists' in str(error_data):
            # Try to list existing links
            list_url = "https://api.dropboxapi.com/2/sharing/list_shared_links"
            list_data = {"path": path}
            list_response = requests.post(list_url, headers=headers, json=list_data)
            
            if list_response.status_code == 200:
                links = list_response.json().get('links', [])
                if links:
                    url = links[0].get('url', '')
                    print(f"✅ Existing shareable link found:")
                    print(f"   {url}")
                    return url
    
    print(f"Error: {response.status_code} - {response.text}")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: create-dropbox-share-link.py <path> [read_only=true]")
        sys.exit(1)
    
    path = sys.argv[1]
    read_only = True if len(sys.argv) < 3 else sys.argv[2].lower() == 'true'
    
    create_shared_link(path, read_only)
