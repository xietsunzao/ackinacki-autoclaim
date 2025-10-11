"""
Popits Auto-Watch Feature Manager (CORRECT FLOW)

Complete flow (user confirmed):
1. Check current mints
2. Watch ~10 unwatched reels (3s delay between each)
3. Call view with amount = target mints (NO WAIT needed!)
   Amount logic (amount = target mint count to reach):
   - mints = 0 → amount = 1 (reach 1 mint: 0→1)
   - mints = 1 → amount = 2 (reach 2 mints: 1→2)
   - mints = 2 → amount = 3 (reach 3 mints: 2→3)
   - mints = 3 → amount = 3 (maintain max)
4. Fetch /me to verify mints increased
5. Strategy:
   - Keep farming reels until mints = 3 (MAX)
   - When mints = 3 → Automatically start tapping
   - Focus: Accumulate mints first, then use them for tapping
"""

import time
import random
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .vdf import calculate_merkle_proof, generate_tap_hash

console = Console()


class PopitsManager:
    """Manages Popits watching cycles with correct complete flow"""

    def __init__(self, api, config):
        """
        Initialize Popits Manager

        Args:
            api: AckinackiAPI instance
            config: Configuration dictionary
        """
        self.api = api
        self.config = config
        self.stats = {
            'reels_watched': 0,
            'views_completed': 0,
            'mints_earned': 0,
            'nfts_minted': 0,
            'vdf_failures': 0
        }

    def run_cycle(self):
        """Run one complete popits cycle"""
        console.print("\n[bold cyan]═══════════════════════════════════[/]")
        console.print("[bold cyan]   Starting Popits Cycle   [/]")
        console.print("[bold cyan]═══════════════════════════════════[/]\n")

        try:
            # Check if banned
            if not self._check_ban_status():
                return False

            # Get current mints status
            me = self.api.get_popits_me()
            if not me:
                console.print("[yellow]Could not fetch popits status[/]")
                return False

            current_mints = me['mints']
            console.print(f"[cyan]Current mints: {current_mints}[/]")

            # Check if already at max - skip watching, go straight to tapping
            if current_mints >= 3:
                console.print(f"\n[bold yellow]🎯 Already at MAX MINTS ({current_mints}/3)![/]")
                console.print(f"[cyan]Skipping reel watching - going straight to tapping[/]\n")
                console.print(f"[bold blue]→ Phase 1: Tapping to Mint NFTs[/]")
                self.do_tapping_challenges(current_mints)

                # Display statistics
                self.display_stats()
                return True

            # Step 1: Watch unwatched reels (only if mints < 3)
            console.print("\n[bold blue]→ Phase 1: Watch Unwatched Reels[/]")
            watch_count = self.config.get('reels_to_watch_per_cycle', 10)
            watched = self._watch_unwatched_reels(watch_count)

            if watched == 0:
                console.print("[yellow]No reels were watched, skipping cycle[/]")
                return False

            console.print(f"[green]✓ Watched {watched} reel(s)[/]")

            # Step 2: Call view to earn mints based on current mints count
            console.print("\n[bold blue]→ Phase 2: View Popits to Earn Mints[/]")

            # Determine amount (target mints) based on current mints
            # amount = target mint count you want to reach
            if current_mints == 2:
                view_amount = 3  # 2 → 3 (reach max)
            elif current_mints == 1:
                view_amount = 2  # 1 → 2 (increment by 1)
            else:  # mints = 0
                view_amount = 1  # 0 → 1 (get first mint)

            console.print(f"[cyan]Calling view with amount: {view_amount} (current: {current_mints} → target: {view_amount} mints)[/]")

            success, status_code, response = self.api.view_popits(amount=view_amount)

            if success:
                console.print(f"[green]✓ View successful! (Status: {status_code})[/]")
                self.stats['views_completed'] += 1

                # Wait a bit for the view to process
                time.sleep(3)

                # Step 3: Check mints after viewing
                console.print("\n[bold blue]→ Phase 3: Check Mints Status[/]")
                me_after = self.api.get_popits_me()
                if me_after:
                    mints_after = me_after['mints']
                    mints_earned = mints_after - current_mints

                    # Show mint status
                    console.print(f"[cyan]Before: {current_mints} mints → After: {mints_after} mints[/]")

                    if mints_earned > 0:
                        self.stats['mints_earned'] += mints_earned
                        console.print(f"[green]✓ Mints increased by +{mints_earned}![/]")
                    elif mints_earned < 0:
                        console.print(f"[yellow]⚠ Mints decreased by {mints_earned} (used for something)[/]")
                    else:
                        console.print(f"[yellow]⚠ Mints unchanged (no increase detected)[/]")

                    # Step 4: Check if we should do tapping
                    console.print(f"\n[bold green]💰 Current Balance: {mints_after} / 3 mints[/]")

                    if mints_after >= 3:
                        # MAX MINTS REACHED - Time to tap!
                        console.print(f"[bold yellow]🎯 MAX MINTS REACHED! Starting tapping...[/]")
                        console.print(f"\n[bold blue]→ Phase 4: Tapping to Mint NFTs[/]")
                        self.do_tapping_challenges(mints_after)
                    else:
                        # Still farming mints
                        remaining = 3 - mints_after
                        console.print(f"[cyan]📊 Strategy: Keep farming reels to reach max[/]")
                        console.print(f"[dim]   Need {remaining} more mint(s) to reach maximum (3)[/]")
                        console.print(f"[dim]   Continue watching reels in next cycle...[/]")
            else:
                console.print(f"[red]✗ View failed (Status: {status_code})[/]")
                if response:
                    console.print(f"[yellow]Response: {response}[/]")

            # Display statistics
            self.display_stats()

            return True

        except Exception as e:
            console.print(f"[red]Error in Popits cycle: {e}[/]")
            import traceback
            traceback.print_exc()
            return False

    def _check_ban_status(self):
        """Check if account is banned"""
        me = self.api.get_popits_me()
        if not me:
            console.print("[yellow]Could not fetch popits status[/]")
            return False

        if me.get('unban_at'):
            console.print(f"[red]⚠️  ACCOUNT BANNED until {me['unban_at']}[/]")
            return False

        return True

    def _select_random_collection(self):
        """Select a random collection from available popcoin collections"""
        collections = self.api.get_popcoins(cursor=0)
        if not collections or not collections.get('data'):
            return None

        # Pick random collection
        return random.choice(collections['data'])

    def _watch_unwatched_reels(self, target_count=10):
        """
        Watch unwatched reels

        Args:
            target_count (int): How many reels to watch (default: 10)

        Returns:
            int: Number of reels actually watched
        """
        watched_count = 0
        watch_delay = self.config.get('watch_delay', 3)

        # Get popits (all collections)
        popits_data = self.api.get_popits(cursor=0, limit=50)
        if not popits_data or not popits_data.get('data'):
            console.print("[yellow]Could not fetch popits[/]")
            return 0

        # Filter unwatched popits (user_minted == 0)
        unwatched = [
            p for p in popits_data['data']
            if p.get('user_minted', 1) == 0
        ]

        if not unwatched:
            console.print("[yellow]No unwatched popits found[/]")
            return 0

        # Randomize order
        random.shuffle(unwatched)
        console.print(f"[cyan]Found {len(unwatched)} unwatched popits[/]")
        console.print(f"[cyan]Will watch {min(target_count, len(unwatched))} reel(s)[/]\n")

        # Watch reels with delay
        for i, popit in enumerate(unwatched[:target_count]):
            try:
                popit_id = popit['id']
                symbol = popit.get('token_symbol', 'Unknown')

                console.print(f"[cyan]  Reel {i+1}/{min(target_count, len(unwatched))}: {symbol}[/]", end=' ')

                # Watch the reel
                success, status_code, _ = self.api.watch_popit(popit_id)

                if success:
                    console.print(f"[green]✓[/]")
                    watched_count += 1
                    self.stats['reels_watched'] += 1
                else:
                    console.print(f"[red]✗ ({status_code})[/]")

                # Delay before next watch (except for last one)
                if i < min(target_count, len(unwatched)) - 1:
                    time.sleep(watch_delay)

            except Exception as e:
                console.print(f"[red]Error: {e}[/]")
                continue

        return watched_count

    def do_tapping_challenges(self, available_mints):
        """
        Do tapping challenges to mint NFTs

        Use mints to do VDF tapping (submit + verify)
        """
        max_vdf = min(available_mints, self.config.get('max_vdf_per_cycle', 3))
        console.print(f"[cyan]Will attempt {max_vdf} tapping challenge(s)[/]\n")

        for i in range(max_vdf):
            console.print(f"[bold cyan]→ Tapping Challenge {i+1}/{max_vdf}[/]")

            # Get a fresh popit for tapping
            popits_data = self.api.get_popits(cursor=0, limit=50)
            if not popits_data:
                console.print("[yellow]Could not fetch popits[/]")
                break

            # Filter unwatched popits only
            available = [
                p for p in popits_data['data']
                if p.get('user_minted', 1) == 0
            ]

            if not available:
                console.print("[yellow]No more unwatched popits available[/]")
                break

            # Pick random popit
            popit = random.choice(available)
            popit_id = popit['id']
            symbol = popit.get('token_symbol', 'Unknown')

            console.print(f"[dim]Selected: {symbol}[/]")

            # Do full tapping flow: watch → session → tap → submit → verify
            success = self.complete_tapping_challenge(popit_id, symbol)

            if success:
                self.stats['nfts_minted'] += 1
                console.print(f"[green]✓ Successfully minted NFT![/]\n")
            else:
                self.stats['vdf_failures'] += 1
                console.print(f"[red]✗ Tapping challenge failed[/]\n")

            time.sleep(2)

    def complete_tapping_challenge(self, popit_id, symbol):
        """
        Complete full tapping challenge workflow

        User's confirmed flow:
        1. Watch 1 popit
        2. Create VDF session
        3. Wait 15 seconds (timer completion)
        4. Generate 1-2 taps only
        5. Submit with leaves_amount: 2
        6. Verify with 1 hash
        """
        try:
            # 1. Watch popit
            console.print("[cyan]  1. Watching popit...[/]")
            success, status_code, _ = self.api.watch_popit(popit_id)
            if not success:
                console.print(f"[red]     Failed to watch ({status_code})[/]")
                return False
            console.print("[green]     ✓ Watched[/]")

            # 2. Create VDF session
            console.print("[cyan]  2. Creating VDF session...[/]")
            session = self.api.create_vdf_session(popit_id)
            if not session:
                console.print("[red]     Failed to create session[/]")
                return False

            session_id = session['id']
            seed = session['seed']
            target_bits = session['targetBits']
            console.print(f"[green]     ✓ Session: {session_id[:8]}... (targetBits: {target_bits})[/]")

            # 3. Generate random taps (under 100 to avoid bot detection)
            console.print("[cyan]  3. Simulating human taps...[/]")
            num_taps = random.randint(
                self.config.get('vdf_min_taps', 40),
                self.config.get('vdf_max_taps', 85)
            )
            console.print(f"[dim]     Target: {num_taps} taps (safe under 100)[/]")

            # 4. Animate tapping over 15 seconds with visual progress
            console.print("[cyan]  4. Tapping animation (15 seconds)...[/]")

            start_time = time.time()
            total_duration = 15  # 15 seconds total
            hashes = []

            # Generate taps progressively over 15 seconds
            taps_per_second = num_taps / total_duration
            current_seed = seed

            while len(hashes) < num_taps:
                elapsed = time.time() - start_time
                remaining = max(0, total_duration - elapsed)

                # Calculate how many taps we should have by now
                expected_taps = int(elapsed * taps_per_second)

                # Generate taps to catch up
                while len(hashes) < expected_taps and len(hashes) < num_taps:
                    # Random tap coordinates (human-like)
                    x = 781 + random.randint(-50, 50)
                    y = 128 + random.randint(-30, 30)
                    timestamp = int(time.time() * 1000)

                    tap_data = generate_tap_hash(current_seed, target_bits, x, y, timestamp)
                    hashes.append(tap_data)
                    current_seed = tap_data['hash']  # Chain for next tap

                # Display animated progress
                progress_percent = (len(hashes) / num_taps) * 100
                progress_bar = '█' * int(progress_percent / 5) + '░' * (20 - int(progress_percent / 5))
                console.print(
                    f"[yellow]     👆 Tapping... [{progress_bar}] {len(hashes)}/{num_taps} "
                    f"({remaining:.1f}s)[/]",
                    end='\r'
                )

                # Small delay to not burn CPU
                time.sleep(0.05)

            # Ensure we have exactly the target number
            console.print(f"[green]     ✓ Completed {len(hashes)} taps in 15 seconds!          [/]")

            # 5. Submit proof with actual number of hashes
            console.print("[cyan]  5. Submitting proof...[/]")
            root_hash = hashes[-1]['hash']
            leaves_amount = len(hashes)  # Submit actual tap count
            result = self.api.submit_vdf_proof(session_id, root_hash, leaves_amount)
            if not result:
                console.print("[red]     Failed to submit proof[/]")
                return False

            selected_amount = result.get('selected_amount', 0)
            console.print(f"[green]     ✓ Proof submitted (selected: {selected_amount})[/]")

            # 6. Verify with ONLY the selected amount of hashes
            console.print("[cyan]  6. Verifying taps...[/]")

            # Use only the number of hashes the API selected
            selected_hashes = hashes[:selected_amount] if selected_amount > 0 else hashes[:1]
            proof, leaves = calculate_merkle_proof(selected_hashes)

            # Debug: Show what we're sending
            console.print(f"[dim]     → API selected {selected_amount} hash(es)[/]")
            console.print(f"[dim]     → Sending {len(selected_hashes)} hash(es) for verification[/]")
            console.print(f"[dim]     → Proof length: {len(proof)} chars[/]")
            console.print(f"[dim]     → Leaves: {len(leaves)} item(s)[/]")

            # Debug: Show first hash structure
            if selected_hashes:
                console.print(f"[dim]     → First hash sample: {selected_hashes[0]}[/]")

            verify_result = self.api.verify_vdf_taps(session_id, selected_hashes, proof, leaves)

            if not verify_result:
                console.print("[red]     ✗ Verification failed - No response[/]")
                return False

            # Show full verification response
            console.print(f"[yellow]     → Verify Response: {verify_result}[/]")

            taps_verified = verify_result.get('taps', 0)
            if taps_verified > 0:
                console.print(f"[green]     ✓ Verified {taps_verified} taps![/]")
                return True
            else:
                console.print(f"[red]     ✗ Verification returned 0 taps[/]")
                return False

        except Exception as e:
            console.print(f"[red]Error in tapping challenge: {e}[/]")
            import traceback
            traceback.print_exc()
            return False

    def display_stats(self):
        """Display session statistics"""
        console.print("\n")

        table = Table(title="Popits Session Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right", style="green")

        table.add_row("Reels Watched", str(self.stats['reels_watched']))
        table.add_row("Views Completed", str(self.stats['views_completed']))
        table.add_row("Mints Earned", f"+{self.stats['mints_earned']}")
        table.add_row("NFTs Minted", str(self.stats['nfts_minted']))
        table.add_row("VDF Failures", str(self.stats['vdf_failures']),
                     style="yellow" if self.stats['vdf_failures'] > 0 else "green")

        console.print(table)
        console.print()
