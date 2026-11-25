import os
import shutil
import errno
import stat

EXT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS_FOLDER = os.path.join(EXT_ROOT, "cards")
WILD_STR = "__"
COLL_PREV_folder = os.path.join(EXT_ROOT, "COLLECTED_PREVIEWS")
PREVIEW_EXTENSIONS = (".jpeg", ".jpg", ".png", ".webp", ".gif")

from .wildcard_manager import wildcard_manager

def silentremove(filename):
    try:
        if os.path.exists(filename):
            os.chmod(filename, stat.S_IWRITE)
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT: 
            raise

_cached_gallery_cards = None

def invalidate_cards_cache():
    global _cached_gallery_cards
    _cached_gallery_cards = None

def collect_gallery_cards(use_cache=True):
    global _cached_gallery_cards
    if use_cache and _cached_gallery_cards is not None:
        return _cached_gallery_cards

    all_wildcards = wildcard_manager.wildcards.keys()
    if hasattr(wildcard_manager, 'hidden_wildcards'):
        all_wildcards = [w for w in all_wildcards if w not in wildcard_manager.hidden_wildcards]
        
    _cached_gallery_cards = sorted(list(all_wildcards))
    return _cached_gallery_cards

def get_safe_name_2(selected_wild_path):
    path_parts = selected_wild_path.split('/')
    parent = path_parts[-2] if len(path_parts) > 1 else ""
    return path_parts[-1], parent

def clean_residue(cards_dir=CARDS_FOLDER):
    """
    Purges any legacy 0-byte dummy .card files to maintain pure virtual cards.
    Removes empty subdirectories. Skips walk if directory does not exist.
    """
    if not os.path.exists(cards_dir):
        return

    for root, dirs, files in os.walk(cards_dir, topdown=False):
        for file in files:
            if file.lower().endswith(".card"):
                silentremove(os.path.join(root, file))

        for dirname in dirs:
            dir_to_check = os.path.join(root, dirname)
            try:
                if not os.listdir(dir_to_check):
                    os.rmdir(dir_to_check)
            except OSError:
                pass

def resolve_card_base_path(wpath, cards_dir=CARDS_FOLDER):
    base_dir = os.path.abspath(cards_dir)
    target = os.path.abspath(os.path.join(base_dir, wpath.replace("/", os.path.sep)))
    if os.path.commonpath([base_dir, target]) != base_dir or target == base_dir:
        return None
    return target

def find_card_previews(wpath, cards_dir=CARDS_FOLDER):
    base_path = resolve_card_base_path(wpath, cards_dir=cards_dir)
    if not base_path:
        return []
    return [base_path + ext for ext in PREVIEW_EXTENSIONS if os.path.isfile(base_path + ext)]

def collect_previews(wildpath_selector, cards_dir=CARDS_FOLDER):
    collected_previews_list = []
    os.makedirs(COLL_PREV_folder, exist_ok=True)
    
    for wpath in wildpath_selector:
        matches = find_card_previews(wpath, cards_dir=cards_dir)
        if matches:
            candidate = matches[0]
            collected_previews_list.append(candidate)
            try:
                rel = os.path.relpath(candidate, cards_dir)
                dest_file_path = os.path.join(COLL_PREV_folder, rel)
                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                shutil.copy2(candidate, dest_file_path)
            except OSError:
                print(f"[SD Forge Wildcards Error] Failed to collect [{candidate}]")

    msg = f"{len(collected_previews_list)} previews were collected" if collected_previews_list else "no wildcard previews were collected"
    return msg

def delete_previews(wildpath_selector, cards_dir=CARDS_FOLDER):
    deleted_count = 0
    for wpath in wildpath_selector:
        for candidate in find_card_previews(wpath, cards_dir=cards_dir):
            try:
                silentremove(candidate)
                deleted_count += 1
            except OSError:
                print(f"[SD Forge Wildcards Error] Failed to delete [{candidate}]")

    msg = f"{deleted_count} previews were deleted" if deleted_count else "no wildcard previews were deleted"
    return msg

