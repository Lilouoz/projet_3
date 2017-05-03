<?php
class BilletsManager extends DbManager

{
	    /**
     * return all billets in db
     *
     * @return array
     */
    public function getBillets() {
        $db = $this->db;
        $query = ('SELECT id, image, alt, titre,contenu, auteur,  date_creation FROM billets ORDER BY date_creation DESC LIMIT 0, 4');
        $req = $db->prepare($query);
        $req->execute();
		
        while($row = $req->fetch(PDO::FETCH_ASSOC)) 
		
		{
            // instance of a billet object
			$billet= new Billet();
			
			// hydrate manualy from bdd datas

			$billet->setId($row['id']);
			$billet->setImage($row['image']);
			$billet->setAlt($row['alt']);
			$billet->setTitre($row['titre']);
			$billet->setContenu($row['contenu']);
			$billet->setAuteur($row['auteur']);
			$billet->setDateCreation($row['date_creation']);
			
			 // now you have an array of object (instead of an array of array)
            $billets[] = $billet;

        }
		
		
        return $billets;
    }
	
	    /**
     * return last billet in db
     *
     * @return array
     */
    public function getLastBillet() 
	{
        $db = $this->db;
        $query = ('SELECT id, image, alt, titre, contenu, auteur, date_creation FROM billets ORDER BY date_creation DESC LIMIT 0, 1');
        $req = $db->prepare($query);
        $req->execute();
		
        while($row = $req->fetch(PDO::FETCH_ASSOC)) 
		
		{
            // instance of a last billet object
			$billet= new Billet();
			
			// hydrate manualy from bdd datas

			$billet->setId($row['id']);
			$billet->setImage($row['image']);
			$billet->setAlt($row['alt']);
			$billet->setTitre($row['titre']);
			$billet->setContenu($row['contenu']);
			$billet->setAuteur($row['auteur']);
			$billet->setDateCreation($row['date_creation']);


        }
		
		
        return $billet;
    }
	
	
	
	
	
    /**
     * save the billet in db
     *
     * @param Billet $billet
     */
    public function persist(Billet $billet)
    {
        if($billet->getId() == null) {
            $this->create($billet);
        } else {
            $this->update($billet);
        }
    }
    /**
     * update a billet in db
     * @param Billet $billet
     * @return $this
     */
	
    public function update(Billet $billet) 
	
	{
        $db = $this->db;
        $req = $db->prepare("UPDATE `billets` SET `id`=[value-1],`image`=[value-2],`alt`=[value-3],`titre`=[value-4],`contenu`=[value-5],`auteur`=[value-6],`date_creation`=[value-7] WHERE 1");
        $req->execute
			
			(
			
            array(
                'id'          	=> $billet->getId(),
				'image'       	=> $billet->getImage(),
                'alt' 		  	=> $billet->getAlt(),
				'titre'       	=> $billet->getTitre(),
                'contenu' 	  	=> $billet->getContenu(),
                'auteur'      	=> $billet->getAuteur(),
                'date_creation' => $billet->getDateCreation()
                
            )
        );
		
		
        return $this;
    }
	
	
    /**
     * create a new billet in db
     *
     * @param Billet $billet
     * @return $this
     */
    public function create(Billet $billet) 
	
	{
        $db = $this->db;
        $req = $db->prepare("INSERT INTO `billets`(`id`, `image`, `alt`, `titre`, `contenu`, `auteur`, `date_creation`) VALUES ([value-1],[value-2],[value-3],[value-4],[value-5],[value-6],[value-7])");
        $req->execute
			
			(
			
            array(
                'image'       	=> $billet->getImage(),
                'alt' 		  	=> $billet->getAlt(),
				'titre'       	=> $billet->getTitre(),
                'contenu' 	  	=> $billet->getContenu(),
                'auteur'      	=> $billet->getAuteur(),
                'date_creation' => $billet->getDateCreation(),
                'id'          	=> $billet->getId()
            )
        );
		
		
        return $this;
    }
	
	
	/**
	*
	* get billet by Id
	*
	*@param $billet_id
	*@return $billet
	*/
	
    public function getBilletById($billet_id)
    {
        $db = $this->db;
        $query = "SELECT * FROM billet WHERE id = ".$billet_id;
        $req = $db->prepare($query);
        $req->execute();
		
		
        $row = $req->fetch(PDO::FETCH_ASSOC);
		
        $billet = new Billet();
        $billet->hydrate($row);
		
		
        return $billet;
    }
	
	
	/**
     * delete a billet in db
     *
     * @param Billet $billet
     * @return $this
     */
	
	/* a ajouter apres connection
    public function create(Billet $billet) 
	
	{
        $db = $this->db;
        $req = $db->prepare("DELETE FROM `billets` WHERE 1");
        $req->execute
			
			(
			
            array(
                'image'       	=> $billet->getImage(),
                'alt' 		  	=> $billet->getAlt(),
				'titre'       	=> $billet->getTitre(),
                'contenu' 	  	=> $billet->getContenu(),
                'auteur'      	=> $billet->getAuteur(),
                'date_creation' => $billet->getDate_creation(),
                'id'          	=> $billet->getId()
            )
        );
		
		
        return $this;
    }
	
	
	public function setDb(PDO $db)
  {
    $this->_db = $db;
  }
	
	*/
	
	
}