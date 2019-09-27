# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

class DiscuzSpider:
    def _get_html(self, url):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print('网络异常')
            return None
        if '抱歉，指定的主题不存在或已被删除或正在被审核' in resp.text or '抱歉，您没有权限访问该版块' in resp.text:
            print('页面不存在或者无权访问')
            return None
        else:
            return resp.text

    def parse_post_info(self, tid):
        """
        获取一个帖子的基本信息
        :param tid: 帖子的 id
        :return: 包含帖子信息的 dict
        """
        url = 'https://www.discuz.net/thread-{}-1-1.html'.format(tid)
        html = self._get_html(url)
        if not html: return {}
        soup = BeautifulSoup(html, 'lxml')
        title = soup.find(id='thread_subject').get_text()  # 帖子标题
        uid_link = soup.find(class_="authi").a['href']  # 用户主页链接 home.php?mod=space&uid=xxxx
        uid = uid_link.split('=')[-1]  # 用户的 uid
        nickname = soup.find(class_='authi').get_text().strip('\n')  # 用户昵称
        content = soup.find('div', class_='t_fsz').get_text()  # 帖子内容
        data = {
            'tid': tid,  # 帖子 id
            'title': title,  # 帖子标题
            'uid': uid,  # 发帖人 uid
            'nickname': nickname,  # 发帖人昵称
            'content': content  # 帖子内容
        }
        return data

    def parse_comment(self, url):
        """
        处理一个页面所有的评论(包含层叠的评论)
        :param url: 页面的链接
        :return: 此页面所有评论的信息，每一条信息是一个 dict，包含 uid 、nickname、comment
        """
        html = self._get_html(url)
        if not html: return None
        print('正在处理:' + url)
        soup = BeautifulSoup(html, 'lxml')
        comments = []  # 要返回的评论信息列表
        table_plhin_list = soup.find_all('table', class_='plhin')  # 评论信息存在在 <table class='plhin'> 下面
        for table_plhin in table_plhin_list:
            a_comment = []
            nickname = table_plhin.find('div', class_='authi').get_text().strip('\n')  # 用户的昵称
            uid_link = table_plhin.find('div', class_="authi").a['href']  # 用户主页链接 home.php?mod=space&uid=xxxx
            uid = uid_link.split('=')[-1]  # 从链接提取用户的 uid
            content = table_plhin.find('div', class_='pcb').get_text()  # 评论的内容
            a_comment.append({'uid': uid, 'nickname': nickname, 'content': content})
            # 处理层叠的评论
            cascaded_comment_list = table_plhin.find_all('div', class_='pstl xs1 cl')
            for cascaded_comment in cascaded_comment_list:
                _uid_link = cascaded_comment.find('a', class_='xi2 xw1')['href']  # 用户的link
                _uid = _uid_link.split('=')[-1]
                _nickname = cascaded_comment.find('a', class_='xi2 xw1').get_text()  # 用户昵称
                _content = cascaded_comment.find('div', class_='psti').get_text()  # 层叠的评论
                a_comment.append({'uid': _uid, 'nickname': _nickname, 'content': _content})
            comments += a_comment
        print("评论数据:" + str(comments))
        return comments

    def get_all_url(self, tid):
        """
        返回一个帖子的所有页的链接
        :param tid: 帖子 id
        :return: 包含所有页面链接的 list
        """
        this_url = 'http://www.discuz.net/thread-{}-1-1.html'.format(tid)
        html = self._get_html(this_url)
        if not html: return None
        soup = BeautifulSoup(html, 'lxml')
        last_page = soup.find('span', title=True)   # <span title="共 373 页" class="xh-highlight"> / 373 页</span>
        if last_page:
            last_page = last_page.get_text().strip(' /页')       # 去除空白字符和"/"、"页",得到最大页数
            return ['http://www.discuz.net/thread-{}-{}-1.html'.format(tid, i) for i in range(1, int(last_page) + 1)]
        else:
            return [this_url]

    def parse(self, tid):
        all_data = {}
        post_info = self.parse_post_info(tid)
        print('帖子信息:' + str(post_info))
        all_data.update(post_info)
        comments = []
        url_list = self.get_all_url(tid)
        if not url_list:    # 如果帖子不存在，是拿不到url_list的
            return None
        for url in url_list:
            comments += self.parse_comment(url)
        comments.pop(0)         # 第1条评论实际上是楼主的帖子，这个在post_info中存过一次，剔除
        all_data['comments'] = comments
        return all_data


if __name__ == '__main__':
    spider = DiscuzSpider()
    data = spider.parse(3846582)
    print('*'*200 + '\n所有数据:' + str(data))
