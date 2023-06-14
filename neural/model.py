import random
import time

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, optimizers, losses, models, Sequential, activations

import simulation

MAX_PLAYERS = 2
RANKS_COUNT = 9
INPUTS = MAX_PLAYERS * 4 * RANKS_COUNT + 6 * 2 * (RANKS_COUNT * 4) + MAX_PLAYERS * len(simulation.PlayerState) + 1  # cards, slots, states, deck,
OUTPUTS = simulation.get_all_possible_turns_count(RANKS_COUNT)


def make_model():
    L = 30
    model = Sequential([
    ])
    model.add(layers.Input((INPUTS,)),)
    for i in range(L):
        a = (i + 1/2) / L
        N = OUTPUTS * a + INPUTS * (1 - a)
        model.add(layers.Dense(N, activation=activations.elu),)
    model.add(layers.Dense(OUTPUTS, activation=activations.softmax))
    return model

def get_model_inputs(game: simulation.Game, player_index):
    players_cards_inputs = []
    players_states_inputs = []
    for index, player in enumerate(game.players.iterfrom(player_index)):
        cards_inputs = np.zeros(RANKS_COUNT * 4, dtype=np.float32)
        for card in player.cards:
            cards_inputs[card.get_index(game.ranks_count)] = 1
        players_cards_inputs.append(cards_inputs)
        states_inputs = np.zeros(len(simulation.PlayerState))
        states_inputs[player.state.value] = 1
        players_states_inputs.append(states_inputs)

    slots_cards = []
    for slot in game.slots:
        slots_cards.append(slot.attack)
        slots_cards.append(slot.defence)
    slots_cards = slots_cards + [None] * (12 - len(slots_cards))

    slots_cards_inputs = []
    for index, card in enumerate(slots_cards):
        card_input = np.zeros(RANKS_COUNT * 4, dtype=np.float32)
        if card is not None:
            card_input[card.get_index(game.ranks_count)] = 1
        slots_cards_inputs.append(card_input)

    deck_inputs = [np.array([len(game.deck) / (RANKS_COUNT * 4)], dtype=np.float32)]
    inputs = players_cards_inputs + slots_cards_inputs + players_states_inputs + deck_inputs

    res = np.concatenate(inputs, axis=0) - 1/2

    return res

def get_index_from_probs(probs):
    s = sum(probs)
    probs = [p / s for p in probs]
    r = random.random()
    s1 = 0
    for i, p in enumerate(probs):
        s1 += p
        if s1 > r:
            return i
    return len(probs) - 1

def get_turn(model, game, available_turns, player_index):
    inputs = get_model_inputs(game, player_index)
    inputs = np.reshape(inputs, (1, INPUTS))
    res = model(inputs)
    res_numpy = res.numpy()[0]
    probabilities = [res_numpy[index] for index, turn in available_turns]
    turn_index_in_available = get_index_from_probs(probabilities)
    turn_absolute_index, turn = available_turns[turn_index_in_available]
    return turn

def get_turn_and_gradients(model, game, available_turns, player_index):
    with tf.GradientTape() as tape:
        inputs = get_model_inputs(game, player_index)
        inputs = np.reshape(inputs, (1, INPUTS))
        res = model(inputs)
        res_numpy = res.numpy()[0]
        probabilities = [res_numpy[index] for index, turn in available_turns]
        turn_index_in_available = get_index_from_probs(probabilities)
        turn_absolute_index, turn = available_turns[turn_index_in_available]
        true_outputs = np.zeros((1, OUTPUTS), dtype=np.float32)
        true_outputs[0, turn_absolute_index] = 1
        loss = losses.mean_squared_error(true_outputs, res)
        gradients = tape.gradient(loss, model.trainable_weights)
    return gradients, turn

def train_on_one_game(model, optimizer):
    gradients_for_players = [None] * MAX_PLAYERS
    game = simulation.Game(15 - RANKS_COUNT, RANKS_COUNT, MAX_PLAYERS)
    while not game.game_ended():
        players_turns_order = list(range(MAX_PLAYERS))
        random.shuffle(players_turns_order)
        for i in players_turns_order:
            if game.players.get_by_id(i).state == simulation.PlayerState.WON:
                continue
            if game.game_ended():
                break
            turns = game.get_available_turns(i)
            if len(turns) == 0:
                continue
            elif len(turns) == 1:
                game.apply_turn(turns[0][1])
            else:
                gradients, turn = get_turn_and_gradients(model, game, turns, i)
                if gradients_for_players[i] is None:
                    gradients_for_players[i] = list(gradients)
                else:
                    for j in range(len(gradients)):
                        gradients_for_players[i][j] = gradients_for_players[i][j] + gradients[j]
                game.apply_turn(turn)
    for i in range(MAX_PLAYERS):
        gradients = gradients_for_players[i]
        won = len(game.players.get_by_id(i).cards) == 0
        if not won:
            gradients = [g * -(MAX_PLAYERS - 1) for g in gradients]
        optimizer.apply_gradients(zip(gradients, model.trainable_weights))

def evaluate_on_one_game(model1, model2):
    game = simulation.Game(15 - RANKS_COUNT, RANKS_COUNT, MAX_PLAYERS)
    while not game.game_ended():
        players_turns_order = list(range(MAX_PLAYERS))
        random.shuffle(players_turns_order)
        for i in players_turns_order:
            if game.players.get_by_id(i).state == simulation.PlayerState.WON:
                continue
            if game.game_ended():
                break
            turns = game.get_available_turns(i)
            if len(turns) == 0:
                continue
            elif len(turns) == 1:
                game.apply_turn(turns[0][1])
            else:
                model = model1 if i % 2 == 0 else model2
                turn = get_turn(model, game, turns, i)
                game.apply_turn(turn)
    for i in range(MAX_PLAYERS):
        if game.players.get_by_id(i).state != simulation.PlayerState.WON:
            if i % 2 == 0:
                return "second"
            else:
                return "first"
    return "none"

def test():
    trained_model = models.load_model("models/4000.pb")
    not_trained_model = models.load_model("models/2000.pb")
    iterations = 300
    results = []
    for i in range(iterations):
        print(i)
        results.append(evaluate_on_one_game(trained_model, not_trained_model))
    print("Trained model wins:", results.count("first"))
    print("Not trained model wins:", results.count("second"))
    quit()

if __name__ == "__main__":
    tf.enable_eager_execution()
    seed = 1
    random.seed(seed)
    np.random.seed(seed)
    tf.set_random_seed(seed)

    test()

    model = make_model()
    optimizer = optimizers.Adam(learning_rate=0.000001, epsilon=1e-5)

    #model = models.load_model("models/9500.pb")
    for i in range(0, 10000000000000000):
        print(i, np.sum(model.get_weights()[6]))
        if i % 100 == 0:
            model.save(f"models/{i}.pb")
        train_on_one_game(model, optimizer)
