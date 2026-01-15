# Rubyハイライト確認用テストファイル

# クラス定義
class User
  attr_accessor :name, :email
  attr_reader :id

  # 初期化メソッド
  def initialize(name, email)
    @name = name
    @email = email
    @id = generate_id
  end

  # インスタンスメソッド
  def greet
    puts "こんにちは、#{@name}さん！"
  end

  # クラスメソッド
  def self.create(attributes)
    new(attributes[:name], attributes[:email])
  end

  private

  def generate_id
    SecureRandom.uuid
  end
end

# モジュール定義
module Authenticatable
  def authenticate(password)
    return false if password.nil?
    
    encrypted_password == encrypt(password)
  end

  def encrypt(str)
    Digest::SHA256.hexdigest(str)
  end
end

# 配列とハッシュ
users = [
  { name: "太郎", age: 25, active: true },
  { name: "花子", age: 30, active: false },
  { name: "次郎", age: 28, active: true }
]

# イテレーション
users.each do |user|
  puts "名前: #{user[:name]}, 年齢: #{us  when 1
    "月曜日"
  when 2
    "火曜日"
  when 3
    "水曜日"
  else
    "その他"
  end
end

# ブロックとyield
def with_logging
  puts "開始"
  yield if block_given?
  puts "終了"
end

with_logging do
  puts "処理中..."
end

# ラムダとProc
multiply = ->(x, y) { x * y }
result = multiply.call(5, 3)

add_proc = Proc.new { |a, b| a + b }

# 例外処理
begin
  risky_operation
rescue StandardError => e
  puts "エラー: #{e.message}"
ensure
  cleanup
end

# 正規表現
email_regex = /\A[\w+\-.]+@[a-z\d\-]+(\.[a-z\d\-]+)*\.[a-z]+\z/i
puts "有効" if "test@example.com" =~ email_regex

# シンボル
status = :active
states = [:pending, :approved, :rejected]

# 文字列操作
message = "Hello, World!"
message.upcase!
message.gsub!(/World/, "Ruby")

# 範囲
(1..10).each { |n| print n }
puts
(1...10).to_a

# メソッドチェーン
numbers = [1, 2, 3, 4, 5]
squared_evens = numbers
  .select(&:even?)
  .map { |n| n ** 2 }
  .sum

# ヒアドキュメント
sql = <<~SQL
  SELECT 時に自動でendが入るかチェック）
def test_method
  if true
    puts "test"
  end
end

class TestClass
  def instance_method
    loop do
      break
    end
  end
end

