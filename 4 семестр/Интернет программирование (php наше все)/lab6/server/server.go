package main

import (
	"encoding/json"
	"net/http"
)

type Server struct {
	db *Storage
}

func NewServer(db *Storage) *Server {
	return &Server{db: db}
}

func (s *Server) Start(addr string) error {
	http.HandleFunc("/emails", s.emailsHandler)
	return http.ListenAndServe(addr, nil)
}

func (s *Server) emailsHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {

	case http.MethodGet:
		s.getEmails(w)

	case http.MethodPost:
		s.createEmail(w, r)

	default:
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

func (s *Server) getEmails(w http.ResponseWriter) {
	w.Header().Set("Content-Type", "application/json")

	json.NewEncoder(w).Encode(s.db.Emails)
}

func (s *Server) createEmail(w http.ResponseWriter, r *http.Request) {
	var email Email

	if err := json.NewDecoder(r.Body).Decode(&email); err != nil {
		http.Error(w, "invalid json", http.StatusBadRequest)
		return
	}

	if err := s.db.SaveEmail(email); err != nil {
		http.Error(w, "failed to save email", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(email)
}
