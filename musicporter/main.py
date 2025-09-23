import os
import sys
import argparse
import shutil
import tempfile
import logging

def main(argv=None):    
    parser = argparse.ArgumentParser(description="musicporter: generate smart music playlists and collect matching files for easily syncing to a phone.")
    parser.add_argument("output_path", help="Root output directory (Music, Playlists, etc. will be created here)")
    parser.add_argument("-m", "--music-path", action="append", required=True, help="Path to a music directory to scan (can be specified multiple times)")
    parser.add_argument("-y", "--yaml-config", required=True, help="Path to YAML config file for smart playlists")
    parser.add_argument("-t", "--temp-path", help="Temporary directory for generated playlists (default: new temp dir)")
    parser.add_argument("-p", "--playlists", help="Directory containing static playlists to copy")
    parser.add_argument("-r", "--search-replace", action="append", metavar="SEARCH::REPLACE", help="Search/replace pair for paths in playlists. Can be specified multiple times.")
    parser.add_argument("--skip-scan", action="store_true", help="Skip scanning music library and use existing database")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args(argv)

    # Configure logging based on --verbose
    log_level = logging.INFO if args.verbose else logging.ERROR
    logging.basicConfig(level=log_level, format='%(name)s %(levelname)s: %(message)s', stream=sys.stdout)
    logger = logging.getLogger("musicporter")

    # Argument validation (abort before any file operations)
    if args.search_replace:
        for pair in args.search_replace:
            if "::" not in pair:
                print(f"Invalid --search-replace pair: {pair}. Must be in SEARCH::REPLACE format.")
                sys.exit(1)
            search, _ = pair.split("::", 1)
            if not search:
                print(f"Invalid --search-replace pair: {pair}. SEARCH (before '::') must not be empty.")
                sys.exit(1)

    # Validate YAML config file existence and parse it before any work
    if not os.path.exists(args.yaml_config):
        print(f"Error: YAML config file does not exist: {args.yaml_config}")
        sys.exit(1)
    try:
        import yaml
        with open(args.yaml_config, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
    except Exception as e:
        print(f"Error: Failed to load/parse YAML config file: {args.yaml_config}\n{e}")
        sys.exit(1)

    db_path = os.path.join(args.output_path, "tracks.sqlite")
    
    # 1. Scan music library (unless --skip-scan)
    if args.skip_scan:
        if not os.path.exists(db_path):
            print(f"Error: --skip-scan specified but database file does not exist at {db_path}")
            sys.exit(1)
        else:
            if args.verbose:
                print('Skipping scan, using existing database at', db_path)
    else: # not args.skip_scan
        bak_path = db_path + ".bak"
        if os.path.exists(bak_path):
            if args.verbose:
                print('Removing old database backup')
            os.remove(bak_path)
        if os.path.exists(db_path):
            if args.verbose:
                print('Backing up existing database')
            os.rename(db_path, bak_path)

        print('Scanning for music...')
        from musicporter.mp3_scanner import Mp3Scanner
        scanner = Mp3Scanner(logger=logger)
        tracks = scanner.scan(args.music_path)

        if args.verbose:
            print('Inserting music into database')
        from musicporter.db import TrackDB
        db = TrackDB(db_path)
        db.insert_tracks(tracks)
        db.close()

    # Delete and recreate the output/Playlists directory
    playlists_dir = os.path.join(args.output_path, "Playlists")
    if os.path.exists(playlists_dir):
        shutil.rmtree(playlists_dir)
    os.makedirs(playlists_dir, exist_ok=True)

    # 2. Generate playlists from YAML config to temp folder
    if args.temp_path:
        temp_playlist_dir = args.temp_path
        if os.path.exists(temp_playlist_dir):
            shutil.rmtree(temp_playlist_dir)
        os.makedirs(temp_playlist_dir, exist_ok=True)
    else:
        temp_playlist_dir = tempfile.mkdtemp(prefix="musicporter_playlists_")
    if args.verbose:
        print(f"Generating playlists to temp folder: {temp_playlist_dir}")
    from musicporter.playlist_generator import PlaylistGenerator
    generator = PlaylistGenerator()
    generator.generate_from_config(args.yaml_config, db_path, output_path=temp_playlist_dir)

    # 3. Copy static playlists (if provided) to temp playlist folder
    if args.playlists:
        print(f"Copying static playlists from {args.playlists} to {temp_playlist_dir}")
        for fname in os.listdir(args.playlists):
            if fname.lower().endswith('.m3u8'):
                shutil.copy2(os.path.join(args.playlists, fname), temp_playlist_dir)

    # 4. Collect all referenced music files to output_path/Music, etc.
    print(f"Collecting music files referenced in playlists to {args.output_path}")
    from musicporter.mp3_collector import Mp3Collector
    collector = Mp3Collector(logger=logger)
    collector.collect_files(
        temp_playlist_dir,
        args.output_path,
        music_source_paths=args.music_path,
        delete_orphans=True
    )

    # 5. Rewrite playlists for output_path/Playlists using search/replace pairs
    playlists_out = os.path.join(args.output_path, "Playlists")
    os.makedirs(playlists_out, exist_ok=True)
    
    # delete any existing m3u8 files in playlists_out
    for fname in os.listdir(playlists_out):
        if fname.lower().endswith('.m3u8'):
            os.remove(os.path.join(playlists_out, fname))

    if args.search_replace:
        # these have already been validated above.
        rewrite_pairs = [pair.split("::", 1) for pair in args.search_replace]
        if args.verbose:
            print(f"Rewriting playlists in {temp_playlist_dir} to {playlists_out} with pairs: {rewrite_pairs}")
        else:
            print(f"Rewriting playlists")
        from musicporter.playlist_rewriter import PlaylistRewriter
        rewriter = PlaylistRewriter()
        for fname in os.listdir(temp_playlist_dir):
            if fname.lower().endswith('.m3u8'):
                src = os.path.join(temp_playlist_dir, fname)
                dst = os.path.join(playlists_out, fname)
                # Apply all rewrite pairs in order
                with open(src, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                new_lines = []
                for line in lines:
                    new_line = line
                    for search, replace in rewrite_pairs:
                        new_line = new_line.replace(search, replace)
                    new_lines.append(new_line)
                with open(dst, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
    else:
        # Just copy playlists as-is
        if args.verbose:
            print(f"Copying playlists from {temp_playlist_dir} to {playlists_out}")
        for fname in os.listdir(temp_playlist_dir):
            if fname.lower().endswith('.m3u8'):
                shutil.copy2(os.path.join(temp_playlist_dir, fname), playlists_out)

    print("musicporter done")

if __name__ == "__main__":
    main()
