import re
import requests

class HandleTagEvent:
    
    def __init__ (self, markdown_text:str):
        self.markdown_text = markdown_text

    def get_tag_list(self):
        regex = r'tags:\s*([^\n]+)\n'
        m = re.search(regex, self.markdown_text, re.DOTALL)
        if m:
            tag_list:list = m.group(1).strip().split(' ')
        else:
            tag_list:list = []
        
        return tag_list

    def validate_tag_info(self, tag:str):
        if '#' in tag:
            message = 'Qiitaではタグ名に # は不要なので修正してください'
        else:
            try:
                tag_follower_count = requests.get(f'https://qiita.com/api/v2/tags/{tag}').json()['followers_count']
            except:
                tag_follower_count = 0
            if tag_follower_count < 200:
                message = f'{tag}はフォロワー数が200を下回るタグですが利用しますか'
            else :
                message = 'is_collect'
        
        return message
            
    def count_tag(self):
        tag_list = self.get_tag_list()
        message = f'記事のタグ数は{len(tag_list)}です。'
        if len(tag_list) < 5:
            message += '\nタグはできる限り5つつけましょう'
        
        return message
    

class HandleCodeBlock:

    def __init__ (self, markdown_text: str):
        self.markdown_text = markdown_text
        
    def get_code_block(self):
        regex = r"```(?P<lang>\w+)?\n(?P<code>.*?)\n```"
        matches = re.findall(regex, self.markdown_text, re.DOTALL)
        return matches if matches else "no_code"
        
    def validate_code_lang(self, i:int, match: re.match):
        lang = match[0]
        if lang == '':
            message = f'{i + 1}番目のコードブロックには言語が指定されていません。\nシンタックスハイライトが有効になるよう、適切なコードを指定しましょう。'
        else:
            message = f'{i + 1}番目のコードブロックに指定されているシンタックスハイライトは{lang}です。'
            if lang not in ['javascript', 'js']:
                message += '\n正しいかを確認しましょう。'
            if lang == 'java':
                message += '\n特にJavaとJavaScriptは、ハムとハムスター位違いますよ。注意しましょう。'

        return message            

class HandleParagraph:
    
    def __init__ (self, markdown_text):
        self.markdown_text = markdown_text

    def remove_code_block(self):
        # コードブロックのパターンを定義する
        regex = r"```[\w\s]*\n([\s\S]*?)\n```"
        # コードブロックを除去する
        return re.sub(regex, "", self.markdown_text, flags=re.DOTALL)

    def count_sharp(self):
        # 各段落の # の数をリストに格納する
        regex = r"^(#+)(?!#)(.*)$"
        headings = []
        text_without_code_blocks = self.remove_code_block()
        
        for line in text_without_code_blocks.split("\n"):
            match = re.match(regex, line)
            if match:
            # コードブロック中の # を除外するため、# の前後にスペースを付与する
                heading = match.group(1).strip()
                headings.append(len(heading))
        return headings

    def is_contain_h_one(self):
        headings = self.count_sharp()

        if any(x == 1 for x in headings) :
            message = '段落のマークダウンは ## からはじめるようにしましょう\n # 1つはページ全体を表すため記事には利用しません'
            return message
        else:
            return 'is_collect'

    def is_corrupted_paragraph(self):
        headings = self.count_sharp()

        count = 0
        for i in range(len(headings) - 1):
            if headings[i + 1] - headings[0] > 1:
                count += 1
        if count > 0:
            message = f'段落構成が崩れている箇所が{count}箇所あります\n # は1つずつ増やしましょう'
            return message
        else:
            return 'is_collect'