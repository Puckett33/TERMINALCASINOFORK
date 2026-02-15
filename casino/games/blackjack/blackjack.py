import random
from typing import Optional

from casino.card_assets import assign_card_art
from casino.cards import StandardCard, StandardDeck, Card
from casino.types import GameContext
from casino.utils import clear_screen, cprint, cinput, display_topbar

BLACKJACK_HEADER = """
┌───────────────────────────────┐
│     ♠ B L A C K J A C K ♠     │
└───────────────────────────────┘
"""

BLACKJACK_HEADER_OPTIONS = {
    "header": BLACKJACK_HEADER,
    "margin": 1,
}

SECURITY_GUARD = "👮‍♂️"
SECURITY_MSG = f"""
{SECURITY_GUARD}: Time for you to go.
You have been removed from the casino

"""
YES_OR_NO_PROMPT       = "[Y]es   [N]o"
DECK_NUMBER_SELECTION  = "🤵: How many decks would you like to play with?"
DECK_NUMBER_BOUNDS_MSG = "🤵: That won't work, please be serious. Try again."
INVALID_NUMBER_MSG     = "🤵: Invalid number. Try again."
INVALID_YES_OR_NO      = "🤵: It's a yes or no, pal. You staying?"
STAY_AT_TABLE_PROMPT   = "🤵: Would you like to stay at the table?"
INVALID_CHOICE_MSG     = "🤵: That's not a choice in this game."
BET_PROMPT             = "🤵: How much would you like to bet?"
INVALID_BET_MSG        = "🤵: That's not a valid bet."
NO_FUNDS_MSG           = "🤵: You don't have enough chips to play. Goodbye."

FULL_DECK: StandardDeck = StandardDeck()

def deal_card(turn: list[Card], deck: StandardDeck) -> None:
    """Deal a card to the player."""
    card = deck.draw()
    turn.append(card)

def double_down(ctx: GameContext, player_hand: list[Card], deck: StandardDeck, bet: int) -> int:
    account = ctx.account
    account.withdraw(bet)
    bet = bet * 2
    deal_card(player_hand, deck)
    return bet

def split_hand(ctx: GameContext, player_hand: list[list[Card]], deck: StandardDeck, bet: int) -> None:    
    #takes second card and bet from hand and put in new hand
    account = ctx.account
    account.withdraw(bet)
    second_hand = [player_hand[0].pop()]
    player_hand.append(second_hand)
    #give each hand a new card
    deal_card(player_hand[0], deck)
    deal_card(player_hand[1], deck)

def hand_total(turn: list[StandardCard]) -> int:
    """Calculate the total of each hand."""
    total = 0
    aces = 0
    for card in turn:
        if not isinstance(card, StandardCard):
            raise ValueError(f"Expected StandardCard, got {type(card)}")
        if card.rank in {"J", "Q", "K"}:
            # Face card
            total += 10
        elif card.rank == "A":
            # Ace special case
            total += 11
            aces += 1
        else:
            # Numeric card (2-10)
            total += int(card.rank)
    # Ace adjustment
    while aces > 0 and total > 21:
        total -= 10
        aces -= 1
    return total

def print_dealer_cards(dealer_hand: list[Card]) -> None:
    
    """Print the dealer's cards side by side."""
    if len(dealer_hand) == 0:
        cprint("")
    # first card shown, rest hidden
    first_card = dealer_hand[0].front
    hidden_card = dealer_hand[1].back
    hand_string = "\n".join([
        "  ".join(lines)
        for lines in zip(first_card.strip("\n").splitlines(),
                         hidden_card.strip("\n").splitlines())
    ])
    cprint(hand_string)
    
# exact same as orginal just put as a separate function for split uses
def print_cards_helper(hand: list[Card]) -> list[str]:
    """Print the cards side by side."""
    card_lines = [
        card.front.strip("\n").splitlines()
        for card in hand
    ]
    max_lines = max(len(lines) for lines in card_lines)

    # pad cards
    for lines in card_lines:
        while len(lines) < max_lines:
            lines.append(" " * len(lines[0]))

    # combine lines horizontally
    combined_lines = []
    for i in range(max_lines):
        combined_lines.append(
            "  ".join(card_lines[j][i] for j in range(len(hand)))
        )
    
    hand_string = "\n".join(combined_lines)
    return hand_string

def print_cards(hand: list[Card]) -> None:
    hand_string = print_cards_helper(hand);
    cprint(hand_string)
    
def print_split_cards(hand1: list[Card], hand2: list[Card]) -> None:
    #same functionality as print cards helper
    lines1 = print_cards_helper(hand1).splitlines()
    lines2 = print_cards_helper(hand2).splitlines()

    max_lines = max(len(lines1), len(lines2))

    # pad cards
    while len(lines1) < max_lines:
        lines1.append(" " * len(lines1[0]))
    while len(lines2) < max_lines:
        lines2.append(" " * len(lines2[0]))

    for i in range(max_lines):
        cprint(f"{lines1[i]}    {lines2[i]}")


def print_hand_total(hand: list[Card], label: str = "Total") -> None:
    """Print the total of the hand."""
    total = hand_total(hand)
    if total == 21 and len(hand) == 2:
        total_string = "Blackjack"
    else: 
        total_string = f"{total}"
    cprint(f"{label}: {total_string}")

def print_split_hand_total(hand1: list[Card], hand2: list[Card], label: str = "Total") -> None:
    """Print the total of the hand."""
    total1 = hand_total(hand1)
    total_string1 = f"{total1}"
    
    total2 = hand_total(hand2)
    total_string2 = f"{total2}"
    
    cprint(f"{label} 1: {total_string1}      {label} 2: {total_string2}")


def print_hand(hand: list[Card], hidden: bool = False) -> None:
    """Print a blackjack hand."""
    if hidden:
        print_dealer_cards(hand)
    else:
        print_cards(hand)
        print_hand_total(hand)

def print_split_hand(hand1: list[Card], hand2: list[Card], hidden: bool = False) -> None:
    """Print a blackjack hand."""
    
    print_split_cards(hand1, hand2)
    print_split_hand_total(hand1, hand2)

def display_blackjack_topbar(ctx: GameContext, bet) -> None:
    display_topbar(ctx.account, **BLACKJACK_HEADER_OPTIONS)
    if bet is None:
        return
    for i in range(len(bet)):
       cprint(f"Bet {i+1}: {bet[i]}")

def offer_insurance(ctx, bet, dealer_hand, player_hand, account):
    """Offers insurance when dealer shows Ace."""
    upcard = dealer_hand[0]
    if upcard.rank != "A":
        return 0, False
    
    # display hands
    cprint("Dealer hand:")
    print_hand(dealer_hand, hidden=True)
    cprint("Your hand:")
    print_hand(player_hand)

    cprint("Dealer shows an Ace.")
    cprint("Would you like to buy insurance?")

    choice = cinput(YES_OR_NO_PROMPT)
    while choice not in "YyNn" or choice == "":
        clear_screen()
        display_blackjack_topbar(ctx, bet)
        cprint(INVALID_YES_OR_NO)
        choice = cinput(YES_OR_NO_PROMPT)

    while choice in "Yy":
        max_bet = bet // 2
        insurance_bet_str = cinput(f"You can bet up to {max_bet} chips. How much would you like to bet for insurance?").strip()
        insurance_bet = 0
        try:
            insurance_bet = int(insurance_bet_str)
            if insurance_bet > max_bet:
                cprint(f"The maximum bet is {max_bet} chips.")
                continue
        except ValueError:
            cprint(INVALID_BET_MSG)
            continue
        try:
            account.withdraw(insurance_bet)
        except ValueError:
            cprint(f"Insufficient funds. You only have {account.balance} chips.")
            continue
        return insurance_bet, True # success

    return 0, False

def resolve_insurance_win(account, insurance_bet, insurance_taken):
    """Payout 2:1 insurance if dealer has blackjack."""
    if insurance_taken and insurance_bet > 0:
        # payout = return bet + 2× profit
        account.deposit(insurance_bet * 3)
        return f"Insurance pays out: +{insurance_bet * 2} chips\n"
    else:
        return ""

def resolve_insurance_loss(insurance_bet, insurance_taken):
    """Player loses insurance immediately when dealer does not have blackjack."""
    if insurance_taken and insurance_bet > 0:
        return f"You lose your insurance bet: -{insurance_bet} chips\n"
    else:
        return ""

def ask_for_bet(ctx: GameContext, err_msg: str, min_bet: int, account):
    #same functionality as original, just put in a function
    # returns -1 for invalid response/ bets and the error message
    if err_msg is not None:
        cprint(err_msg) 
        err_msg = None
    bet_str = cinput(BET_PROMPT).strip()
    try:
        bet = int(bet_str)
        if bet < min_bet:
            err_msg = f"The minimum bet is {min_bet} chips."
            return -1, err_msg
    except ValueError:
        err_msg = INVALID_BET_MSG
        return -1, err_msg
    try:
        initial_bet = bet
        account.withdraw(bet)
    except ValueError:
        err_msg = f"Insufficient funds. You only have {account.balance} chips."
        return -1, err_msg
    return bet, err_msg    

def play_blackjack(ctx: GameContext) -> None:
    """Play a blackjack game."""
    account = ctx.account
    min_bet = ctx.config.blackjack_min_bet
    if account.balance < min_bet:
        clear_screen()
        display_blackjack_topbar(ctx, None)
        cprint(NO_FUNDS_MSG)
        cinput("Press enter to continue.")
        return
    continue_game = True
    stubborn = 0 # gets to 7 and you're out
    err_msg = None
    while (True):
        clear_screen()
        display_blackjack_topbar(ctx, None)
        # let user choose number of decks being dealt
        if err_msg is not None:
            cprint(err_msg)
        decks_str = cinput(DECK_NUMBER_SELECTION).strip()
        try:
            decks = int(decks_str)
        except ValueError:
            err_msg = INVALID_NUMBER_MSG
            continue
        if decks <= 0:
            err_msg = DECK_NUMBER_BOUNDS_MSG
            continue
        break
    
    err_msg = None
    while continue_game:
        bet = []
        # determine the bet amount
        initial_hand = True
        while True:
            clear_screen()
            display_blackjack_topbar(ctx, None)
            test_bet, err_msg = ask_for_bet(ctx, err_msg, min_bet, account)
            if test_bet == -1:
                continue
            else:
                bet.append(test_bet)
                break

        clear_screen()
        display_blackjack_topbar(ctx, bet)

        # local variables
        player_status1 = True
        player_status2 = False #is there a second hand
        dealer_status = True
        presplit_bj = False
        dealer_bj = False
        resolve_twice = False # for print message

        # two decks of cards (values + string IDs)
        FULL_DECK = StandardDeck(decks)
        deck = FULL_DECK

        # hands
        player_hand = [[]]
        dealer_hand = []

        # initial deal (player first)
        for _ in range(2):
            deal_card(player_hand[0], deck)
            deal_card(dealer_hand, deck)

        insurance_bet, insurance_taken = offer_insurance(ctx, bet[0], dealer_hand, player_hand[0], account)

        # player BJ check
        if hand_total(player_hand[0]) == 21:
            presplit_bj = True
            player_status1 = False

        # dealer BJ check
        if hand_total(dealer_hand) == 21:
            # dealer blackjack in initial deal
            dealer_bj = True
            player_status1 = False
            dealer_status = False
            cprint("Dealer hand:")
            print_hand(dealer_hand)
            cprint("Your hand:")
            print_hand(player_hand[0])

        # player turn 1
        while player_status1:
            # display hands
            cprint("Dealer hand:")
            print_hand(dealer_hand, hidden=True)
            if not player_status2:
                cprint("Your hand:")
                print_hand(player_hand[0])
            else:
                cprint("Your hands:")
                print_split_hand(player_hand[0], player_hand[1])
                cprint("Hand 1's Turn \n")
            # conditional actions
            account = ctx.account
            if initial_hand and account.balance >= min_bet:
                if  player_hand[0][0].rank == player_hand[0][1].rank and account.balance >= bet[0]:
                    actions_str = "[S]tay   [H]it   [D]ouble Down   S[p]lit"
                    actions = "SsHhDdPp"
                elif account.balance >= bet[0]:
                    actions_str = "[S]tay   [H]it   [D]ouble Down"
                    actions = "SsHhDd"

            else:
                actions_str = "[S]tay   [H]it"
                actions = "SsHh"

            initial_hand = False

            # action choice input
            action = cinput(actions_str)
            print()

            # check valid answer
            while action not in actions or action == "":
                stubborn += 1
                if stubborn >= 13:
                    clear_screen()
                    cprint(SECURITY_MSG)
                    return
                clear_screen()
                display_blackjack_topbar(ctx, bet)
                cprint(INVALID_CHOICE_MSG + "\n")
                print_dealer_cards(dealer_hand)
                if not player_status2:
                    cprint("Your hand:")
                    print_hand(player_hand[0])
                else:
                    cprint("Your hands:")
                    print_split_cards(player_hand[0], player_hand[1])
             
                action = cinput(actions_str)

            clear_screen()
            display_blackjack_topbar(ctx, bet)

            # handle action
            if action.lower() == "s":
                player_status1 = False
            elif action.lower() == "h":
                deal_card(player_hand[0], deck)
            elif action.lower() == "d":
                bet[0] = double_down(ctx, player_hand[0], deck, bet[0])
                clear_screen()
                display_blackjack_topbar(ctx, bet)
            elif action.lower() == "p":
                player_status2 = True
                resolve_twice = True
                split_hand(ctx,player_hand, deck, bet[0])
                bet.append(bet[0])
                
                clear_screen()
                display_blackjack_topbar(ctx,bet)
            else:
                raise ValueError(f"Invalid choice: {action}")

            # player bust condition
            if hand_total(player_hand[0]) > 21:
                player_status1 = False
                if not player_status2:
                    dealer_status = False
                # display hands
                if not player_status2:
                    cprint("Dealer hand:")
                    print_hand(dealer_hand)
                    cprint("Your hand:")
                    print_hand(player_hand[0])

            # player 21 end condition
            if hand_total(player_hand[0]) == 21:
                player_status1 = False

        while player_status2:
            # display hands
            cprint("Dealer hand:")
            print_hand(dealer_hand, hidden=True)
            cprint("Your hands:")
            print_split_hand(player_hand[0], player_hand[1])
            cprint("Hand 2's Turn \n")

            actions_str = "[S]tay   [H]it"
            actions = "SsHh"

            # action choice input
            action = cinput(actions_str)
            print()

            # check valid answer
            while action not in actions or action == "":
                stubborn += 1
                if stubborn >= 13:
                    clear_screen()
                    cprint(SECURITY_MSG)
                    return
                clear_screen()
                display_blackjack_topbar(ctx, bet)
                cprint(INVALID_CHOICE_MSG + "\n")
                print_dealer_cards(dealer_hand)
                cprint("Your hands:")
                print_split_hand(player_hand[0], player_hand[1])
                action = cinput(actions_str)

            clear_screen()
            display_blackjack_topbar(ctx, bet)

            # handle action
            if action.lower() == "s":
                player_status2 = False
                dealer_status = True
            elif action.lower() == "h":
                deal_card(player_hand[1], deck)
            else:
                raise ValueError(f"Invalid choice: {action}")

            # player bust condition
            if hand_total(player_hand[1]) > 21:
                player_status2 = False
                # display hands
                cprint("Dealer hand:")
                print_hand(dealer_hand)
                cprint("Your hands:")
                print_split_hand(player_hand[0], player_hand[1])
                
            # player 21 end condition
            if hand_total(player_hand[1]) == 21:
                player_status2 = False
                dealer_status = True
                
                
        if resolve_twice:
            if hand_total(player_hand[0]) > 21 and hand_total(player_hand[1]) > 21:
                dealer_status = False
        else:
            if hand_total(player_hand[0]) > 21:
                dealer_status = False
                
        # dealer turn
        while dealer_status:
            # dealer status check/update
            if hand_total(dealer_hand) > 21:
                # display hands
                cprint("Dealer hand:")
                print_hand(dealer_hand)
                if not resolve_twice:
                    cprint("Your hand:")
                    print_hand(player_hand[0])
                else:
                    cprint("Your hands:")
                    print_split_hand(player_hand[0], player_hand[1])
                
                dealer_status = False
            elif hand_total(dealer_hand) > 16:
                # display hands
                cprint("Dealer hand:")
                print_hand(dealer_hand)
                if not resolve_twice:
                    cprint("Your hand:")
                    print_hand(player_hand[0])
                else:
                    cprint("Your hands:")
                    print_split_hand(player_hand[0], player_hand[1])
                dealer_status = False
            else:
                deal_card(dealer_hand, deck)

         ############## WIN CHECKS ##############
        print()
        
        win_msgs = []
        # insurance resolution
        if dealer_bj:
            insurance_msg = resolve_insurance_win(account, insurance_bet, insurance_taken)
            win_msgs.append(insurance_msg)
        else:
            insurance_msg = resolve_insurance_loss(insurance_bet, insurance_taken)
            win_msgs.append(insurance_msg)
            
        num_of_hands = len(player_hand)
        
        for i in range(num_of_hands):  
        # main game resolution
            if presplit_bj and dealer_bj:
                win_msgs.append("Player and dealer have a blackjack\n")
                win_msgs.append("Push\n")
                account.deposit(bet[i])
                # player gets back bet
            elif not presplit_bj and dealer_bj:
                win_msgs.append("Dealer has a blackjack\n")
                win_msgs.append(f"You lose: -{bet[i]} chips\n")
                dealer_won = True
                # player loses bet, +1 loss
            elif presplit_bj and not dealer_bj:
                win_msgs.append("Player has a blackjack\n")
                win_msgs.append(f"You win: +{bet[i]} chips\n")
                account.deposit(bet[i] * 2)
                # player gets back 2x bet, +1 win, +1 bj counter
            elif hand_total(player_hand[i]) > 21:
                win_msgs.append(f"Hand {i+1}: You busted\n")
                win_msgs.append(f"Dealer wins: -{bet[i]} chips\n")
                # player loses bet, +1 loss
            elif hand_total(player_hand[i]) <= 21 and hand_total(dealer_hand) > 21:
                win_msgs.append(f"Hand {i+1}: Dealer busted\n")
                win_msgs.append(f"You win: +{bet[i]} chips\n")
                account.deposit(bet[i] * 2)
                # player gets back 2x bet, +1 win
            elif hand_total(player_hand[i]) == hand_total(dealer_hand):
                win_msgs.append(f"Hand {i+1}: Player and dealer have same number\n")
                win_msgs.append("Push\n")
                account.deposit(bet[i])
                # player gets back bet, +1 draw
            elif hand_total(player_hand[i]) < hand_total(dealer_hand):
                win_msgs.append(f"Hand {i+1}: Dealer wins: -{bet[i]} chips\n")
                # player loses bet, +1 loss
            elif hand_total(player_hand[i]) > hand_total(dealer_hand):
                win_msgs.append(f"Hand {i+1}: Player wins: +{bet[i]} chips\n")
                account.deposit(bet[i] * 2)
                # player gets back 2x bet, +1 win
            else:
                raise ValueError(
                    "Unaccounted for win condition!\n"
                    f"Player: {hand_total(player_hand[i])}   "
                    f"Dealer: {hand_total(dealer_hand)}"
            )

        #redisplay
        
        clear_screen()
        display_blackjack_topbar(ctx, bet)
        cprint("Dealer hand:")
        print_hand(dealer_hand)

        if resolve_twice:
            cprint("Your hands:")
            print_split_hand(player_hand[0], player_hand[1])
        else:
            cprint("Your hand:")
            print_hand(player_hand[0])

        for msg in win_msgs:
            cprint(msg)

        # game restart?
        if account.balance < min_bet:
            cprint(NO_FUNDS_MSG)
            cinput("Press enter to continue.")
            continue_game = False
            continue
        cprint(STAY_AT_TABLE_PROMPT)
        play_again = cinput(YES_OR_NO_PROMPT)
        # check valid answer
        while play_again not in "YyNn" or play_again == "":
            stubborn += 1
            if stubborn >= 13:
                clear_screen()
                cprint(SECURITY_MSG)
                return
            clear_screen()
            display_blackjack_topbar(ctx, bet)
            cprint(INVALID_YES_OR_NO)
            play_again = cinput(YES_OR_NO_PROMPT)

        # play / leave
        if play_again in "Nn":
            clear_screen()
            cprint(f"\nThanks for playing.\n\n")
            continue_game = False
