# -*- coding: utf-8 -*-

# 必要ライブラリのインポート
import os
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import networkx as nx
from networkx.algorithms import community
from networkx.drawing.nx_agraph import graphviz_layout
from pyvis.network import Network
import wordcloud
import datetime, pytz
from IPython.display import display


# 乱数を固定する
seed = 42
os.environ['PYTHONHASHSEED'] = str(seed)
random.seed(seed)
np.random.seed(seed)

# フォントパスを取得する
# font_path='/Library/Fonts/Arial Unicode.ttf',
# font_path = !find ${HOME} -name "ipaexg.ttf"
# font_path = [os.path.join(root, file) for root, dirs, files in os.walk(".") for file in files if file == 'ipaexg.ttf']
font_path = [os.path.join(root, file) for root, dirs, files in os.walk("/usr/local") for file in files if file == 'ipaexg.ttf']


# ワードクラウドを描画する
def plot_wordcloud(word_str, width=6, height=4):

    # プロットの準備
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_subplot(1, 1, 1)

    # 指定したプロット位置(ax)にワードクラウドを描画する
    plot_wordcloud_ax(ax, word_str)

    # プロットの仕上げ
    plt.axis("off")
    plt.tight_layout()
    plt.show()

# 指定したプロット位置(ax)にワードクラウドを描画する
def plot_wordcloud_ax(ax, word_str):

    # ワードクラウドを作成する
    wc = wordcloud.WordCloud(
        background_color='white',
        font_path=font_path[0],
        random_state=42,
        max_font_size=100)

    # ワードクラウドを描画する
    img = wc.generate(word_str)
    ax.imshow(img, interpolation='bilinear')


# トピックモデルによるワードクラウドを描画する
def plot_topic_model(lda, feature_names, n_top_words=20, width=10, height=4):

    fig = plt.figure(figsize=(width, height))

    # トピックごとのループ
    for topic_idx, topic in enumerate(lda.components_):

        # トピック中で出現確率の高い頻に単語をソートし,
        # ワードクラウドに描画するためテキストを生成する
        sorted_text = ' '.join([feature_names[i] for i in topic.argsort()[:-n_top_words-1:-1]])

        # ワードクラウドを作成する
        wc = wordcloud.WordCloud(
            background_color='white',
            font_path=font_path[0],
            random_state=42,
            max_font_size=100)

        # プロット位置(ax)を選ぶ
        ax = fig.add_subplot(2, 3, topic_idx + 1)

        # ワードクラウドを描画する
        img = wc.generate(sorted_text)
        ax.imshow(img, interpolation='bilinear')
        ax.set_title(f"Topic # {topic_idx+1}:")

    # プロットの仕上げ
    plt.tight_layout()
    plt.show()


# 共起ネットワーク図を描画する (抽出語-抽出語用)
def plot_cooccur_network(df, word_counts, cutoff, width=8, height=8, dep=False, pyvis=False, name="pyvis.html"):

    # プロットの準備
    plt.figure(figsize=(width, height))
    fig = plt.figure(figsize=(width, height))

    # プロット位置(ax)を選ぶ
    ax = fig.add_subplot(1, 1, 1)

    # 指定したプロット位置(ax)に共起ネットワーク図を描画する
    pyvis_plot = plot_cooccur_network_ax(ax, df, word_counts, cutoff, dep, pyvis, name)

    # プロットの仕上げ
    plt.axis("off")
    plt.show()

    # # PyVis プロットを出力する
    # if pyvis:
    #     display(pyvis_plot)

# 指定したプロット位置(ax)に共起ネットワーク図を描画する
def plot_cooccur_network_ax(ax, df, word_counts, cutoff, dep=False, pyvis=False, name="pyvis.html"):

    # 共起行列の中身(numpy行列)を取り出す
    Xc = df.values

    # 共起行列中の最大値を求める
    Xc_max = Xc.max()

    # プロットする単語リストを取得する
    words = df.columns

    # プロットする単語の出現頻度の最大値を求める (正規化用)
    count_max = word_counts.max()

    weights_w, weights_c = [], []

    # 共起行列の要素ごとのループ (値がゼロの要素はスキップ)
    for i, j in zip(*Xc.nonzero()):
        # 対角行列でかつ値がしきい値を超えるものを保持する
        if i != j and Xc[i,j] > cutoff:
            # ノード: 一方の単語とノードの大きさ(正規化した出現頻度)を保持する
            weights_w.append((words[i], {'title': words[i], 'size': word_counts[i] / count_max * 100}))
            # ノード: 他方の単語とノードの大きさ(正規化した出現頻度)を保持する
            weights_w.append((words[j], {'title': words[j], 'size': word_counts[j] / count_max * 100}))
            # エッジ: 両端の単語を結ぶエッジの太さ(正規化した共起行列の値)を保持する
            weights_c.append((words[i], words[j], Xc[i,j] / Xc_max * 3))

    # グラフの作成
    if dep:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    G.add_nodes_from(weights_w)
    G.add_weighted_edges_from(weights_c)
    G.remove_nodes_from(list(nx.isolates(G)))
    # G = nx.minimum_spanning_tree(G)

    # サブグラフの検出
    communities = community.greedy_modularity_communities(G)

    # ノードにサブグラフのグループを設定する
    for node in G:
        G.nodes[node]['shape'] = 'circle'
        for i, c in enumerate(communities):
            if node in c:
                G.nodes[node]['group'] = i

    # エッジのタイトルに重みの値を設定する
    for u, v in G.edges():
        G[u][v]['title'] = f"{G[u][v]['weight']/3:0.2f}"

    # プロット用にノートとエッジの重みをリストに変換する
    weights_n = np.array(list(nx.get_node_attributes(G, 'size').values()))
    weights_e = np.array(list(nx.get_edge_attributes(G, 'weight').values()))
    color_map = np.array(list(nx.get_node_attributes(G, 'group').values()))

    # グラフの描画
    # pos = nx.spring_layout(G, k=0.3)
    # pos = graphviz_layout(G, prog='neato', args='-Goverlap="scalexy" -Gsep="+6" -Gnodesep=0.8 -Gsplines="polyline" -GpackMode="graph" -Gstart={}'.format(43))
    pos = graphviz_layout(G, prog='neato', args='-Goverlap="scalexy" -Gsep="+6" -Gnodesep=0.8 -GpackMode="graph" -Gstart={}'.format(43))
    nx.draw_networkx_nodes(G, pos, node_color=color_map, alpha=0.7, cmap=plt.cm.Set2, node_size=weights_n * 50, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', edge_cmap=plt.cm.Blues, alpha=0.7, width=weights_e, ax=ax)
    nx.draw_networkx_labels(G, pos, font_family='IPAexGothic', ax=ax)
    # ax.axis('off')

    pyvis_plot = None
    if pyvis:
        # PyVis ネットワークの作成
        net = Network(notebook=True, cdn_resources='in_line', directed=dep)
        net.from_nx(G)
        net.show_buttons(filter_=['nodes', 'edges', 'physics'])
        pyvis_plot = net.show(f"{name}")
    return pyvis_plot

# 指定したプロット位置(ax)に共起ネットワーク図を描画する
def plot_cooccur_network_with_code_ax(ax, df, word_counts, cutoff, coding_rule=None, dep=False, pyvis=False, name="pyvis.html"):

    # 共起行列の中身(numpy行列)を取り出す
    Xc = df.values

    # 共起行列中の最大値を求める
    Xc_max = Xc.max()

    # プロットする単語リストを取得する
    words = df.columns

    # プロットする単語の出現頻度の最大値を求める (正規化用)
    count_max = word_counts.max()

    weights_w, weights_c = [], []

    # 共起行列の要素ごとのループ (値がゼロの要素はスキップ)
    for i, j in zip(*Xc.nonzero()):
        # 対角行列でかつ値がしきい値を超えるものを保持する
        if i != j and Xc[i,j] > cutoff:
            # ノード: 一方の単語とノードの大きさ(正規化した出現頻度)を保持する
            weights_w.append((words[i], {'title': words[i], 'size': word_counts[i] / count_max * 100}))
            # ノード: 他方の単語とノードの大きさ(正規化した出現頻度)を保持する
            weights_w.append((words[j], {'title': words[j], 'size': word_counts[j] / count_max * 100}))
            # エッジ: 両端の単語を結ぶエッジの太さ(正規化した共起行列の値)を保持する
            weights_c.append((words[i], words[j], Xc[i,j] / Xc_max * 3))

    # グラフの作成
    if dep:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    G.add_nodes_from(weights_w)
    G.add_weighted_edges_from(weights_c)
    G.remove_nodes_from(list(nx.isolates(G)))
    # G = nx.minimum_spanning_tree(G)

    # サブグラフの検出
    communities = community.greedy_modularity_communities(G)

    # ノードにサブグラフのグループを設定する
    for node in G:
        G.nodes[node]['shape'] = 'circle'
        for i, c in enumerate(communities):
            if node in c:
                G.nodes[node]['group'] = i

    # エッジのタイトルに重みの値を設定する
    for u, v in G.edges():
        G[u][v]['title'] = f"{G[u][v]['weight']/3:0.2f}"

    # プロット用にノートとエッジの重みをリストに変換する
    nodelist_c = [node for node in G.nodes if node in coding_rule]
    nodelist_w = [node for node in G.nodes if node not in coding_rule]
    weights_c = np.array([G.nodes[node]['size'] for node in G.nodes if node in coding_rule])
    weights_w = np.array([G.nodes[node]['size'] for node in G.nodes if node not in coding_rule])
    weights_e = np.array(list(nx.get_edge_attributes(G, 'weight').values()))

    color_map_c = []
    for node in G:
        if node in coding_rule:
            for i, c in enumerate(communities):
                if node in c:
                    color_map_c.append(i)
            G.nodes[node]['shape'] = 'box'
    color_map_w = []
    for node in G:
        if node not in coding_rule:
            for i, c in enumerate(communities):
                if node in c:
                    color_map_w.append(i)

    # グラフの描画
    # pos = nx.spring_layout(G, k=0.3)
    pos = graphviz_layout(G, prog='neato', args='-Goverlap="scalexy" -Gsep="+6" -Gnodesep=0.8 -Gsplines="polyline" -GpackMode="graph" -Gstart={}'.format(43))
    nx.draw_networkx_nodes(G, pos, node_color=color_map_c, alpha=0.7, cmap=plt.cm.Set2, node_size=weights_c * 50, ax=ax, nodelist=nodelist_c, node_shape='s', edgecolors='red')
    nx.draw_networkx_nodes(G, pos, node_color=color_map_w, alpha=0.7, cmap=plt.cm.Set2, node_size=weights_w * 50, ax=ax, nodelist=nodelist_w)
    nx.draw_networkx_edges(G, pos, edge_color='gray', edge_cmap=plt.cm.Blues, alpha=0.7, width=weights_e, ax=ax)
    nx.draw_networkx_labels(G, pos, font_family='IPAexGothic', ax=ax)
    # ax.axis('off')

    pyvis_plot = None
    if pyvis:
        # PyVis ネットワークの作成
        net = Network(notebook=True, cdn_resources='in_line', directed=dep)
        net.from_nx(G)
        net.show_buttons(filter_=['nodes', 'edges', 'physics'])
        pyvis_plot = net.show(f"{name}")
    return pyvis_plot

# 共起ネットワークを描画する (外部変数-抽出語用)
def plot_attrs_network(df, attr_counts, word_counts, cutoff, width=8, height=8, pyvis=False, name="pyvis.html"):

    # 共起行列の中身(numpy行列)を取り出す
    Xc = df.values

    # 共起行列中の最大値を求める
    Xc_max = Xc.max()

    # プロットする属性(外部変数等)リストを取得する
    attrs = list(df.index)

    # プロットする属性(外部変数等)の最大数を求める (正規化用)
    attr_count_max = attr_counts.max()

    # プロットする単語リストを取得する
    words = list(df.columns)

    # プロットする単語の出現頻度の最大値を求める (正規化用)
    word_count_max = word_counts.max()

    weights_n, weights_c = [], []

    # 共起行列の要素ごとのループ
    for i, j in zip(*Xc.nonzero()):
        # 値がしきい値を超えるものを保持する (値がゼロの要素はスキップ)
        if Xc[i,j] > cutoff:
            # ノード: 属性(外部変数等)とノードの大きさ(正規化した属性数)を保持する
            weights_n.append((attrs[i], {'title': attrs[i],'size': attr_counts[i] / attr_count_max * 10, 'type': 'attr'}))
            # ノード: 単語とノードの大きさ(正規化した出現頻度)を保持する
            weights_n.append((words[j], {'title': words[j],'size': word_counts[j] / word_count_max * 100, 'type': 'word'}))
            # エッジ: 属性(外部変数等)と単語を結ぶエッジの太さ(正規化した共起行列の値)を保持する
            weights_c.append((attrs[i], words[j], Xc[i,j] / Xc_max * 3))

    # プロットの準備
    plt.figure(figsize=(width, height))

    # グラフの作成
    G = nx.Graph()
    G.add_nodes_from(weights_n)
    G.add_weighted_edges_from(weights_c)
    G.remove_nodes_from(list(nx.isolates(G)))
    # G = nx.minimum_spanning_tree(G)

    # 属性と単語を色分けする
    for node in G:
        G.nodes[node]['shape'] = 'circle'
        if G.nodes[node]['type'] == 'word':
            G.nodes[node]['group'] = G.degree(node)+3   # "+3"はカラーマップをシフトする調整値

    # エッジのタイトルに重みの値を設定する
    for u, v in G.edges():
        G[u][v]['title'] = f"{G[u][v]['weight']/3:0.2f}"

    # プロット用にノートとエッジの重みをリストに変換する
    nodelist_a = [node for node in G.nodes if G.nodes[node]['type'] == 'attr']
    nodelist_w = [node for node in G.nodes if G.nodes[node]['type'] == 'word']
    weights_a = np.array([G.nodes[node]['size'] for node in G.nodes if G.nodes[node]['type'] == 'attr'])
    weights_w = np.array([G.nodes[node]['size'] for node in G.nodes if G.nodes[node]['type'] == 'word'])
    weights_e = np.array(list(nx.get_edge_attributes(G, 'weight').values()))
    color_map = np.array(list(nx.get_node_attributes(G, 'group').values()))

    # グラフの描画
    # pos = nx.spring_layout(G, k=0.3)
    pos = graphviz_layout(G, prog='neato', args='-Goverlap="scalexy" -Gsep="+6" -Gnodesep=0.8 -Gsplines="polyline" -GpackMode="graph" -Gstart={}'.format(43))
    nx.draw_networkx_nodes(G, pos, node_color='lightsalmon', alpha=0.7, cmap=plt.cm.Set2, node_size=weights_a * 100, nodelist=nodelist_a, node_shape='s', edgecolors='red')
    nx.draw_networkx_nodes(G, pos, node_color=color_map, alpha=0.7, cmap=plt.cm.Set2, node_size=weights_w * 50, nodelist=nodelist_w)
    nx.draw_networkx_edges(G, pos, edge_color='gray', edge_cmap=plt.cm.Blues, alpha=0.7, width=weights_e)
    nx.draw_networkx_labels(G, pos, font_family='IPAexGothic')

    # プロットの仕上げ
    plt.axis("off")
    plt.show()

    if pyvis:
        # PyVis ネットワークの作成
        net = Network(notebook=True, cdn_resources='in_line')
        net.from_nx(G)
        net.show_buttons(filter_=['nodes', 'edges', 'physics'])
        pyvis_plot = net.show(f"{name}")
        # display(pyvis_plot)

# 係り受けによる共起ネットワーク図を描画する (抽出語-抽出語用)
def plot_dependency_network(df, word_counts, cutoff, width=8, height=8, pyvis=False, name="pyvis.html"):
    plot_cooccur_network(df, word_counts, cutoff, dep=True, width=width, height=height, pyvis=pyvis, name=name)

# 指定したプロット位置(ax)に係り受けによる共起ネットワーク図を描画する
def plot_dependency_network_ax(ax, df, word_counts, cutoff, pyvis=False, name="pyvis.html"):
    return plot_cooccur_network_ax(ax, df, word_counts, cutoff, dep=True, pyvis=pyvis, name=name)

# 指定したプロット位置(ax)に係り受けによる共起ネットワーク図を描画する
def plot_dependency_network_with_code_ax(ax, df, word_counts, cutoff, coding_rule=None, pyvis=False, name="pyvis.html"):
    return plot_cooccur_network_with_code_ax(ax, df, word_counts, cutoff, coding_rule=coding_rule, dep=True, pyvis=pyvis, name=name)


# 対応分析の結果をプロットする
def plot_coresp(row_coord, col_coord, row_labels, col_labels, explained_inertia=None, width=8, height=8):

    # プロットの準備
    plt.figure(figsize=(width, height))

    # 行方向(外部変数)のプロット
    plt.plot(row_coord[:, 0], row_coord[:, 1], "*", color='red', alpha=0.5)
    for i, label in enumerate(row_labels):
        plt.text(row_coord[i, 0], row_coord[i, 1], label, color='red', ha='left', va='bottom')

    # 列方向(単語)のプロット
    plt.plot(col_coord[:, 0], col_coord[:, 1], "o", color='blue', alpha=0.5)
    for i, label in enumerate(col_labels):
        plt.text(col_coord[i, 0], col_coord[i, 1], label, color='blue', ha='left', va='bottom')

    # 原点を通る水平と垂直線を引く
    plt.axvline(0, linestyle='dashed', color='gray', alpha=0.5)
    plt.axhline(0, linestyle='dashed', color='gray', alpha=0.5)

    # 軸ラベルに寄与率を追記する
    if explained_inertia is not None:
        plt.xlabel(f"Dim 1 ({explained_inertia[0]:.3f}%)")
        plt.ylabel(f"Dim 2 ({explained_inertia[1]:.3f}%)")

    # プロットの仕上げ
    # plt.axis('equal')
    plt.show()


# PCA の結果をプロットする
def plot_pca(coeff, reduced, row_labels, col_labels, var_ratio=None, width=8, height=8):

    # プロットの準備
    plt.figure(figsize=(width, height))

    # 行方向(外部変数)のプロット
    for i, label in enumerate(row_labels):
        plt.arrow(0, 0, coeff[i,0], coeff[i,1], color='r', alpha=0.5)
        plt.text(coeff[i, 0], coeff[i, 1], label, color='red', ha='left', va='bottom')

    # 列方向(単語)のプロット
    plt.plot(reduced[:, 0], reduced[:, 1], "o", color='blue', alpha=0.5)
    for i, label in enumerate(col_labels):
        plt.text(reduced[i, 0], reduced[i, 1], label, color='blue', ha='left', va='bottom')

    # 原点を通る水平と垂直線を引く
    plt.axvline(0, linestyle='dashed', color='gray', alpha=0.5)
    plt.axhline(0, linestyle='dashed', color='gray', alpha=0.5)

    # 軸ラベルに寄与率を追記する
    if var_ratio is not None:
        plt.xlabel(f"Dim 1 ({var_ratio[0]*100:.3f}%)")
        plt.ylabel(f"Dim 2 ({var_ratio[1]*100:.3f}%)")

    # プロットの仕上げ
    # plt.axis('equal')
    plt.show()


# 共起頻度行列を Jaccard 係数行列に変換する (抽出語-抽出語用)
def jaccard_coef(cooccur_df, cross_df):

    # 共起行列の中身(numpy行列)を取り出す
    Xc = cooccur_df.values

    # Jaccard 係数行列を初期化する (共起行列と同じ形)
    Xj = np.zeros(Xc.shape)

    # 単語ごとに共起度を集計する
    Xc_sum = cross_df.sum(axis=0).values

    # 共起行列の要素ごとのループ (値がゼロの要素はスキップ)
    for i, j in zip(*Xc.nonzero()):
        # 対角行列の要素を取り出す
        if i < j:
            # Jaccard 係数を求める
            Xj[i,j] = Xc[i,j] / (Xc_sum[i] + Xc_sum[j] - Xc[i,j])

    # DataFrame 型に整える
    jaccard_df = pd.DataFrame(Xj, columns=cooccur_df.columns, index=cooccur_df.columns)

    return jaccard_df


# 共起頻度行列を Jaccard 係数行列に変換する (外部変数-抽出語用)
def jaccard_attrs_coef(df, attr_counts, word_counts, total=10000, conditional=False):

    # 共起行列の中身(numpy行列)を取り出す
    Xc = df.values

    # Jaccard 係数行列を初期化する (共起行列と同じ形)
    Xj = np.zeros(df.shape)

    # 共起行列の要素ごとのループ (値がゼロの要素はスキップ)
    for i, j in zip(*Xc.nonzero()):

        # conditional フラグが True の場合, 条件付き確率 > 前提確率 以外はゼロにする
        if not conditional:

            # 条件付き確率を求める
            conditional_prob = Xc[i,j] / attr_counts[i]

            # 前提確率を求める
            assumption_prob = word_counts[j] / total

            # 条件付き確率 > 前提確率の場合
            if conditional_prob > assumption_prob:
                # Jaccard 係数を求める
                Xj[i,j] = Xc[i,j] / (attr_counts[i] + word_counts[j] - Xc[i,j])

            # 条件付き確率 <= 前提確率の場合
            else:
                # ゼロにする
                Xj[i,j] = .0

        # conditional フラグが False の場合, すべてのケースで Jaccard 係数を求める (デフォルト)
        else:
            # Jaccard 係数を求める
            Xj[i,j] = Xc[i,j] / (attr_counts[i] + word_counts[j] - Xc[i,j])

    # DataFrame 型に整える
    jaccard_df = pd.DataFrame(Xj, columns=df.columns, index=df.index)

    return jaccard_df


# トピック分布を描画する
def plot_topic_distribution(topic_distribution, width=6, height=4):

    # プロットの準備
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_subplot(1, 1, 1)

    # 指定したプロット位置(ax)にワードクラウドを描画する
    plot_topic_distribution_ax(ax, topic_distribution)

    # プロットの仕上げ
    # plt.axis("off")
    plt.tight_layout()
    plt.show()

# 指定したプロット位置(ax)にトピック分布を描画する
def plot_topic_distribution_ax(ax, topic_distribution):

    n_topics = len(topic_distribution)

    # 棒グラフ
    x = np.arange(n_topics)
    bars = ax.bar(x, topic_distribution)
    ax.set_xlabel('トピック')
    ax.set_ylabel('割合')
    # ax.set_ylim(0, 0.5)
    ax.set_xticks(x, [f'#{i+1}' for i in range(n_topics)])
    ax.grid(True, linestyle='--', alpha=0.3)

    # 棒の上に値を表示
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height, f'{height*100:.1f}%', ha='center', va='bottom')
