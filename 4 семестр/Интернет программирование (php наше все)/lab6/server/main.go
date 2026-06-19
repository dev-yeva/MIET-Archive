package main

import "fmt"

func main() {
	storage := LoadStorage("database.json")
	server := NewServer(storage)

	fmt.Println("Server started on http://localhost:8080/emails")

	if err := server.Start(":8080"); err != nil {
		fmt.Println(err)
	}
}
